#!/usr/bin/env python3
"""skill_miner.py - mine Hermes sessions for repeated workflows and DRAFT new skills.

Idea (from @omarsar0 / OpenAI Codex "package skills from interactions"): the best
source of new skills is your own repeated instructions. This scans recent session
transcripts, clusters near-duplicate user instructions, and for any workflow you've
asked for >= MIN_HITS times, drafts a SKILL.md with the LOCAL model (qwen3:8b = $0).

SAFETY: drafts are written to skills/_drafts/<slug>/SKILL.md for REVIEW ONLY. Nothing
is ever installed as an active skill automatically. A dedup ledger means each cluster
is drafted once. Read a draft, and if good, move it up into skills/<name>/.

Run:  python3 skill_miner.py            (review-only; safe to schedule weekly)
Env:  SKILL_MINER_MIN_HITS (default 3), FLEET_MODEL (default qwen3:8b)
"""
import os, re, json, glob, sqlite3, hashlib, datetime, urllib.request

HERMES = os.environ.get("LOCALAPPDATA", os.path.expanduser("~")) + r"\hermes"
HERMES = os.environ.get("HERMES_HOME", HERMES)
STATE_DB = os.path.join(HERMES, "state.db")
SESS_DIR = os.path.join(HERMES, "sessions")
DRAFTS = os.path.join(HERMES, "skills", "_drafts")
SEEN = os.path.join(DRAFTS, ".miner_seen.json")
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("FLEET_MODEL", "qwen3:8b")
MIN_HITS = int(os.environ.get("SKILL_MINER_MIN_HITS", "3"))

STOP = set("the a an to of for and or is are be do my me i you it this that with on in "
           "can could please help write make create get set how what when why need want "
           "hey hi ok thanks thank pls".split())


def _seen():
    try:
        return set(json.load(open(SEEN, encoding="utf-8")))
    except Exception:
        return set()


def _save_seen(s):
    os.makedirs(DRAFTS, exist_ok=True)
    json.dump(sorted(s), open(SEEN, "w", encoding="utf-8"))


def collect_user_messages():
    """Best-effort: pull user-authored text from state.db, then request dumps."""
    msgs = []
    # 1) sqlite state.db - scan every table/column for plausible message text.
    try:
        con = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        tabs = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for t in tabs:
            try:
                cols = [c[1] for c in con.execute(f"PRAGMA table_info('{t}')")]
            except Exception:
                continue
            textcols = [c for c in cols if any(k in c.lower() for k in ("content", "text", "message", "body", "prompt"))]
            rolecol = next((c for c in cols if c.lower() in ("role", "author", "sender", "speaker")), None)
            if not textcols:
                continue
            sel = ",".join(f'"{c}"' for c in (textcols + ([rolecol] if rolecol else [])))
            try:
                rows = con.execute(f'SELECT {sel} FROM "{t}" LIMIT 5000').fetchall()
            except Exception:
                continue
            for r in rows:
                role = (str(r[rolecol]).lower() if rolecol and r[rolecol] is not None else "user")
                if role not in ("user", "human", "brian", "1", "true"):
                    if rolecol:
                        continue
                for c in textcols:
                    v = r[c]
                    if isinstance(v, str) and 12 <= len(v) <= 600:
                        msgs.append(v)
        con.close()
    except Exception as e:
        print(f"[miner] state.db read skipped: {e}")
    # 2) request dumps (messages array sent to the model)
    for p in glob.glob(os.path.join(SESS_DIR, "request_dump_*.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
            for m in (d.get("messages") or d.get("body", {}).get("messages") or []):
                if (m.get("role") == "user"):
                    c = m.get("content")
                    if isinstance(c, list):
                        c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
                    if isinstance(c, str) and 12 <= len(c) <= 600:
                        msgs.append(c)
        except Exception:
            pass
    return msgs


_NOISE = ("arguments", "function", "command not found", "traceback", "pragma",
          "select ", "def ", "```", "stderr", "stdout", "errorlevel", "[silent]",
          "wsl", "bash:", "powershell", "pythonw", "localhost", "http", "{", "}",
          "null", "true,", "0x", ".py", ".ps1", "c:\\", "/mnt/")


def is_instruction(s):
    """Keep natural-language requests; drop tool/system/code/error noise."""
    t = s.strip()
    words = t.split()
    if not (4 <= len(words) <= 80):
        return False
    low = t.lower()
    if any(k in low for k in _NOISE):
        return False
    letters = sum(c.isalpha() or c.isspace() for c in t)
    if letters / max(len(t), 1) < 0.8:   # too many symbols => code/JSON
        return False
    if not re.search(r"\b(fix|add|build|make|create|write|run|check|update|set|"
                     r"deploy|review|find|stop|continue|help|draft|tell|give|"
                     r"install|optimize|improve|process|summari|organi|schedule)\w*", low):
        return False
    return True


def normkey(s):
    toks = [w for w in re.findall(r"[a-z']+", s.lower()) if w not in STOP and len(w) > 2]
    return " ".join(sorted(set(toks))[:6])  # order-independent intent fingerprint


def cluster(msgs):
    groups = {}
    for m in msgs:
        k = normkey(m)
        if not k:
            continue
        groups.setdefault(k, []).append(m.strip())
    return {k: v for k, v in groups.items() if len(v) >= MIN_HITS}


def ollama(prompt):
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0.2, "num_predict": 700}}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["response"]


DRAFT_PROMPT = (
    "You are drafting a reusable Hermes SKILL.md from a user's REPEATED requests.\n"
    "Below are {n} similar instructions Brian has given. Infer the recurring workflow and\n"
    "write ONE skill that would handle it next time. Output EXACTLY this, nothing else:\n\n"
    "---\nname: <kebab-case-name>\ndescription: <one tight sentence with concrete trigger phrases; no colons>\n---\n\n"
    "# <Title>\n\n## When to use\n- ...\n\n## Steps\n1. ...\n\n## Rules\n- Draft only; never send/post/deploy without approval.\n\n"
    "REPEATED INSTRUCTIONS:\n{samples}\n"
)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "skill"


def main():
    seen = _seen()
    msgs = collect_user_messages()
    raw = len(msgs)
    msgs = [m for m in msgs if is_instruction(m)]
    print(f"[miner] collected {raw} messages, {len(msgs)} pass the instruction filter")
    clusters = cluster(msgs)
    print(f"[miner] {len(clusters)} workflow clusters with >= {MIN_HITS} hits")
    os.makedirs(DRAFTS, exist_ok=True)
    drafted = []
    for key, samples in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        h = hashlib.sha1(key.encode()).hexdigest()[:10]
        if h in seen:
            continue
        ex = "\n".join(f"- {s}" for s in samples[:8])
        try:
            out = ollama(DRAFT_PROMPT.format(n=len(samples), samples=ex)).strip()
        except Exception as e:
            print(f"[miner] model error on cluster {h}: {e}")
            continue
        out = re.sub(r"<think>.*?</think>", "", out, flags=re.S).strip()
        m = re.search(r"name:\s*([a-z0-9\-]+)", out)
        name = m.group(1) if m else slug(key)
        d = os.path.join(DRAFTS, name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write(out + f"\n\n<!-- DRAFT from skill_miner.py {datetime.date.today()} | {len(samples)} hits | review before activating: move up to skills/{name}/ -->\n")
        seen.add(h)
        drafted.append((name, len(samples)))
    _save_seen(seen)
    if drafted:
        print("[miner] DRAFTED (review-only) in skills/_drafts/:")
        for n, c in drafted:
            print(f"   - {n}  ({c} hits)")
    else:
        print("[miner] no new draftable workflows this run")


if __name__ == "__main__":
    main()

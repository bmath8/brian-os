#!/usr/bin/env python3
"""Research agent - the local, token-FREE processor for the X research system.

Reads raw captures from comms/research_raw/*.json (written by the paste skill or the
browser-capture flow), summarizes each via the LOCAL model (qwen3:8b, $0) into the
AI-handoff template, and appends high-signal notes to Harmony/06_Research/X_Knowledge_Base.md
(which the fleet RAG-indexes -> brief + chat queries).

Token-efficient + long-term:
  * Local model only (no API cost). Dedup ledger (comms/.research_seen.json) -> each item
    processed exactly once, never re-burned. Low-value items are SKIPPED to keep the KB high-signal.

Raw capture JSON shape (one file per item):
  {"id": "<tweet id or url>", "url": "...", "author": "@handle (Name)", "date": "YYYY-MM-DD",
   "kind": "single|thread|reply|quote", "text": "<the tweet/thread text>"}

Run: python3 research_agent.py            (process whatever's captured; schedulable weekly)
"""
import os, sys, json, glob, datetime, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

RAW = f"{fc.COMMS}/research_raw"
DONE = f"{RAW}/done"
SEEN = f"{fc.COMMS}/.research_seen.json"
KB = os.path.join(fc.HARMONY, "06_Research", "X_Knowledge_Base.md")

PROJECTS = ("AI Job Hunter (flagship AI app, Brian's income engine), Boombox (music app, paused), "
            "Brian OS Fleet (his agent system), Job Hunt (landing a dev job = goal #1), "
            "Learning (skills to retain), General. Stack: React/TS, Next.js, Python, Node, local LLMs/Ollama.")

TEMPLATE = (
    "### <one-line gist>\n"
    "- **Source:** {author} · {date} · {url}  · {kind}\n"
    "- **Project tags:** [pick from: AI Job Hunter | Boombox | Brian OS Fleet | Job Hunt | Learning | General]\n"
    "- **Topic tags:** #tag1 #tag2\n"
    "- **Key insight:** <concrete, 1-3 sentences>\n"
    "- **Why it matters to Brian:** <ties to a project/goal>\n"
    "- **Actionable takeaway:** <what to DO with it>\n"
    "- **Apply by:** <a concrete next step, or 'reference only'>\n"
    "- **Confidence / freshness:** <high|medium> · <evergreen|time-sensitive>\n"
    "- **Raw excerpt:** \"<key quote>\"")


def _seen():
    try:
        return set(json.load(open(SEEN, encoding="utf-8")))
    except Exception:
        return set()


def _save_seen(s):
    fc.atomic_write(SEEN, json.dumps(sorted(s)))


def summarize(item):
    prompt = (
        "You are Brian's long-term research analyst. Distill the X post below into ONE structured "
        "note for his knowledge base, using EXACTLY this template (fill every field, keep it tight):\n\n"
        f"{TEMPLATE}\n\n"
        f"BRIAN'S PROJECTS/GOALS: {PROJECTS}\n\n"
        "Rules: only extract what's genuinely useful to those projects or to a working dev/AI builder. "
        "Be concrete in the takeaway (a tool to try, a technique to apply, an idea to ship). "
        "The FIRST line MUST be a real short title starting with '### ' (replace <one-line gist> with it). "
        "If the post has NOTHING valuable for Brian, reply with exactly 'SKIP' and nothing else.\n\n"
        f"X POST:\nAuthor: {item.get('author','?')}\nDate: {item.get('date','?')}\n"
        f"Kind: {item.get('kind','single')}\nURL: {item.get('url','')}\n\n"
        # The post text is UNTRUSTED external content - wrap it so a tweet can't inject
        # instructions that hijack the analyst role (#47).
        + fc.wrap_untrusted(item.get('text', '')[:4000], "captured X post"))
    out = fc.ollama_generate(prompt, num_ctx=8192, temperature=0.3, num_predict=420,
                             timeout=120, retries=1, fallback="SKIP").strip()
    # Safety: if the model left the heading placeholder, derive a title from the key insight.
    if "<one-line gist>" in out:
        title = "Saved insight"
        for ln in out.splitlines():
            if "Key insight:" in ln:
                t = ln.split("Key insight:")[-1].strip().lstrip("*").strip(" :")
                title = " ".join(t.split()[:10]) or title
                break
        out = out.replace("### <one-line gist>", f"### {title}")
    return out


def main():
    os.makedirs(DONE, exist_ok=True)
    os.makedirs(os.path.dirname(KB), exist_ok=True)
    seen = _seen()
    files = sorted(glob.glob(f"{RAW}/*.json"))
    added, skipped = 0, 0
    for f in files:
        try:
            item = json.load(open(f, encoding="utf-8"))
        except Exception:
            os.replace(f, f"{DONE}/{os.path.basename(f)}")
            continue
        iid = str(item.get("id") or item.get("url") or hashlib.sha1(item.get("text", "").encode()).hexdigest()[:10])
        if iid in seen:
            os.replace(f, f"{DONE}/{os.path.basename(f)}")
            continue
        note = summarize(item)
        seen.add(iid)
        if note.upper().startswith("SKIP"):
            skipped += 1
        else:
            stamp = datetime.datetime.now().strftime("%Y-%m-%d")
            try:
                with open(KB, "a", encoding="utf-8") as kb:
                    kb.write(f"\n\n{note}\n\n_(saved {stamp})_\n")
                added += 1
            except Exception as e:
                print(f"KB write failed: {e}")
        os.replace(f, f"{DONE}/{os.path.basename(f)}")
    _save_seen(seen)
    if added or skipped:
        print(f"\U0001f4da Research: {added} note(s) added to the knowledge base, {skipped} skipped (low-value).")
    fc.state_update("research", {"last_run": datetime.datetime.now().strftime("%Y-%m-%d"),
                                 "status": "ok", "summary": f"{added} added, {skipped} skipped",
                                 "needs_human": []})
    fc.log_run("research", "ok", f"{added} added, {skipped} skipped")


if __name__ == "__main__":
    main()

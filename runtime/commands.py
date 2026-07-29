#!/usr/bin/env python3
"""commands.py - two-way command grammar for the fleet (drive it from Telegram).
Pure logic over the comms blackboard: NO network, NO second Telegram poller (that would
409 against the gateway). `handle(text) -> reply` is called by the Hermes inbound handler
(or run from the CLI). Everything stays inside GUARDRAILS - filing/queuing/grading only;
nothing sends, spends, or deploys.

Grammar:
  /help                     list commands
  /status                   per-agent status + snoozes
  /queue <task...>          drop a task for the overnight worker
  /approve <id>             file an overnight draft as approved (worker learns from it)
  /reject  <id>             file an overnight draft as rejected
  /grade <id> <1|0>         grade a recall card (1=got it, 0=missed)
  /snooze <agent> <days>    mute an agent's "Needs you" items for N days

CLI:  python3 commands.py "/status"
"""
import os, sys, re, glob, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc
import srs

HELP = ("Commands:\n"
        "/status — fleet status\n"
        "/health — system one-liner (RAM/disk/gateway/brief)\n"
        "/digest — end-of-day wrap (done / open / tomorrow)\n"
        "/ask <question> — ask about your world (runway, #1, saved notes…)\n"
        "/tailor <jd> — draft a tailored application kit (fit + resume + cover)\n"
        "/prep <role|jd> — likely interview questions + your angles\n"
        "/code <question> — coding help from qwen3-coder\n"
        "/network <note> — log a networking touch\n"
        "/gigs — latest freelance gig matches\n"
        "/queue <task> — add an overnight task\n"
        "/approve <id> · /reject <id> — file a draft\n"
        "/grade <id> 1|0 — grade a recall card\n"
        "/snooze <agent> <days> — mute its alerts\n"
        "/research <text|url> · /watchlist @handle\n"
        "/help — this list")


def _oneline(fname):
    return " ".join(l for l in fc.read(f"{fc.COMMS}/{fname}").splitlines()
                    if l.strip() and not l.startswith("#")).strip()


def _digest():
    """End-of-day wrap (#38): what the day held, what's still open, tomorrow's focus.
    Pure blackboard read - deterministic, no model, instant."""
    st = fc.load_state().get("agents", {})
    parts = ["🌙 End-of-day digest"]
    career = st.get("career", {}).get("summary", "")
    if career:
        parts.append(f"Job hunt: {career}")
    fin, hea = _oneline("finance.md"), _oneline("health.md")
    if fin:
        parts.append(f"Finance: {fin[:120]}")
    if hea:
        parts.append(f"Health: {hea[:120]}")
    pend = [os.path.basename(p) for p in glob.glob(f"{fc.COMMS}/review/*.md") if "NEEDS REVIEW" in fc.read(p)]
    if pend:
        parts.append(f"To review ({len(pend)}): " + ", ".join(pend[:3]))
    needs = [f"{n}: {item}" for n, a in st.items() for item in (a.get("needs_human") or [])]
    if needs:
        parts.append("Still open: " + "; ".join(needs[:4]))
    parts.append("Tomorrow: 5 tailored applications first.")
    return "\n".join(parts)


def _tailor(arg):
    """Draft a tailored application kit from a JD (#23 fit + #25 tailoring): why-you-fit,
    resume focus/keywords, and a short cover note. Income-critical -> escalates to the big
    model (VRAM gate downgrades if it won't fit). Writes to the approval queue; never sends."""
    if not arg.strip():
        return "Usage: /tailor <paste the job description, or a company + role>"
    resume = fc.read_harmony("03_Career/Resume_DRAFT.md")[:3000]
    jt = fc.read_harmony("03_Career/Job_Tracker.md")
    pm = re.search(r"pitch.*?\n>\s*_?(.+)", jt, re.I | re.S)
    pitch = (pm.group(1).strip(" _>") if pm else "Self-taught full-stack / AI-app developer who ships.")[:300]
    prompt = (
        "You are Brian's job-application assistant. From his RESUME, PITCH, and the JOB DESCRIPTION, "
        "draft a tight application kit in plain text, no preamble:\n"
        "1) FIT: 2 sentences on why he's a strong match + any gap to address.\n"
        "2) RESUME FOCUS: 4-6 bullets/keywords to emphasize for THIS role (ATS-aware).\n"
        "3) COVER NOTE: a 90-110 word note he can adapt.\n"
        "Be specific to the JD. Do NOT invent experience he lacks.\n\n"
        f"PITCH: {pitch}\n\nRESUME:\n{resume}\n\nJOB DESCRIPTION:\n"
        + fc.wrap_untrusted(arg[:3000], "job description"))
    # num_ctx 8192->12288: paid for by flash-attn + q8 KV cache (enabled 2026-07-06).
    kit = fc.ollama_generate(prompt, model=fc.BIG_MODEL, num_ctx=12288, temperature=0.4,
                             num_predict=600, timeout=180, retries=1, fallback="")
    if not kit.strip():
        return "Couldn't draft the kit just now (local model busy) - try again in a moment."
    # Verifier/reflection pass on the income-critical draft (no-op-safe; free, local).
    kit = fc.reflect(kit, task="job application kit")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    title = arg.strip().splitlines()[0][:50]
    os.makedirs(f"{fc.COMMS}/review", exist_ok=True)
    fc.atomic_write(f"{fc.COMMS}/review/tailor-{stamp}.md",
                    f"# Review: Application kit - {title}\nSTATUS: NEEDS REVIEW - drafted {stamp}\n\n{kit.strip()}\n")
    return f"Drafted a tailored application kit (tailor-{stamp}). Review it via /status or comms/review/, then apply."


def _prep(arg):
    """Interview-prep generator (#24): likely questions + STAR angles from Brian's kit + resume."""
    if not arg.strip():
        return "Usage: /prep <role, company, or pasted JD>"
    kit = fc.read_harmony("03_Career/Interview_Prep_Kit.md")[:2500]
    resume = fc.read_harmony("03_Career/Resume_DRAFT.md")[:1500]
    prompt = (
        "You are Brian's interview coach. For the ROLE/JD below, list the 6 most likely interview "
        "questions and, for each, a one-line angle drawing on Brian's REAL projects (from his KIT/RESUME). "
        "Plain text, numbered, concrete (not generic). Do not invent experience.\n\n"
        "ROLE/JD:\n" + fc.wrap_untrusted(arg[:1500], "role/JD")
        + f"\n\nKIT:\n{kit}\n\nRESUME:\n{resume}")
    out = fc.ollama_generate(prompt, model=fc.BIG_MODEL, num_ctx=12288, temperature=0.4,
                             num_predict=550, timeout=180, retries=1,
                             fallback="(couldn't reach the model just now - try again in a moment)")
    return out.strip()[:3800]


def _code(arg):
    """Ask the coding-tuned model (qwen3-coder:30b) a dev question from Telegram."""
    if not arg.strip():
        return "Usage: /code <coding question or snippet> - answered by qwen3-coder."
    prompt = ("You are a senior engineer. Answer Brian's coding question concisely and correctly, "
              "with working code when relevant (React/TypeScript, Next.js, Python, Node). "
              "Plain text, focused, no filler.\n\n" + arg.strip())
    return fc.ollama_generate(prompt, model=fc.CODE_MODEL, num_ctx=8192, temperature=0.3,
                              num_predict=650, timeout=180, retries=1,
                              fallback="(couldn't reach the coding model just now - try again in a moment)")[:3800]


def _network(arg):
    """Log a networking touch (#26); career_agent counts these toward the weekly target."""
    if not arg.strip():
        return "Usage: /network <who you reached out to + a short note>"
    p = f"{fc.COMMS}/networking.md"
    line = f"- {datetime.date.today().isoformat()} · {arg.strip()[:160]}\n"
    fc.atomic_write(p, (fc.read(p) or "# Networking log\n") + line)
    return "Logged a networking touch ✓ — counts toward your weekly target."


def _ask(arg):
    """Conversational query (#34): answer from RAG memory + the live blackboard."""
    if not arg.strip():
        return "Ask me anything, e.g. /ask how's my runway? · /ask what's my #1 today? · /ask what did I save about RAG?"
    try:
        import memory_index
        ctx = memory_index.context_for(arg, fallback="")
    except Exception:
        ctx = ""
    st = fc.load_state().get("agents", {})
    bb = "; ".join(f"{n}: {a.get('summary','')}" for n, a in st.items() if a.get("summary"))
    prompt = ("You are Brian's chief of staff. Answer his question concisely (<=80 words, plain text, no preamble) "
              "from the CONTEXT and CURRENT STATUS below. If the answer isn't there, say briefly what's missing. "
              "Never invent numbers.\n"
              f"QUESTION: {arg}\n\nCURRENT STATUS: {bb or 'n/a'}\n\nCONTEXT:\n{ctx[:3000]}")
    return fc.ollama_generate(prompt, num_ctx=8192, temperature=0.3, num_predict=220, timeout=90,
                              retries=1, fallback="(couldn't reach the local model just now - try again in a moment)")


def _health():
    """On-demand system one-liner (#25 UX): the watchdog's latest checks, instantly,
    without waiting for the 4h cycle. Pure blackboard read - no model, no network."""
    sysmd = fc.read(f"{fc.COMMS}/system_status.md")
    if not sysmd.strip():
        return "No watchdog report yet - it runs every 4h (or run system_watchdog.py)."
    stamp = sysmd.splitlines()[0].replace("# System Status - ", "") if sysmd.splitlines() else ""
    checks = [l[2:] for l in sysmd.splitlines() if l.startswith("- ")]
    alerts = []
    if "## Alerts" in sysmd:
        alerts = [l[2:] for l in sysmd.split("## Alerts", 1)[1].splitlines() if l.startswith("- ")]
        checks = checks[:len(checks) - len(alerts)]
    head = ("✅ ALL CLEAR" if not alerts else f"🚨 {len(alerts)} alert(s)") + f" · as of {stamp}"
    body = "\n".join(checks[:10])
    return head + "\n" + body + ("\n" + "\n".join("⚠ " + a for a in alerts[:4]) if alerts else "")


def _status():
    st = fc.load_state()
    agents = st.get("agents", {})
    if not agents:
        return "No agent state yet."
    snz = fc.snoozed_agents()
    rows = []
    for name in sorted(agents):
        a = agents[name]
        tag = " (snoozed)" if name in snz else ""
        n = len(a.get("needs_human", []) or [])
        rows.append(f"• {name}: {a.get('status','?')} @ {a.get('last_run','-')}"
                    f"{' · ' + str(n) + ' needs' if n else ''}{tag}")
    return "Fleet status:\n" + "\n".join(rows)


def _queue(arg):
    if not arg.strip():
        return "Usage: /queue <task description>"
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    title = arg.strip().splitlines()[0][:60]
    path = f"{fc.COMMS}/queue/{stamp}.md"
    fc.atomic_write(path, f"# {title}\n\n{arg.strip()}\n")
    return f"Queued for tonight's worker: “{title}”."


def _move_review(idarg, outcome):
    idarg = idarg.strip()
    if not idarg:
        return f"Usage: /{outcome.rstrip('d')} <id or filename fragment>"
    cands = [f for f in glob.glob(f"{fc.COMMS}/review/*.md")
             if idarg.lower() in os.path.basename(f).lower()]
    if not cands:
        return f"No pending review matches “{idarg}”."
    if len(cands) > 1:
        return ("Matches several: " + ", ".join(os.path.basename(c) for c in cands[:5]) +
                " — be more specific.")
    dst_dir = f"{fc.COMMS}/review/{outcome}"
    os.makedirs(dst_dir, exist_ok=True)
    base = os.path.basename(cands[0])
    os.replace(cands[0], f"{dst_dir}/{base}")
    return f"Marked “{base}” as {outcome}."


def _grade(arg):
    bits = arg.split()
    if len(bits) < 2 or bits[1] not in ("0", "1"):
        return "Usage: /grade <id> <1|0>"
    cards = srs.load()
    ok = srs.grade(cards, bits[0], correct=(bits[1] == "1"))
    if not ok:
        return f"No recall card with id {bits[0]}."
    srs.save(cards)
    return f"Graded {bits[0]}: {'got it ✓' if bits[1]=='1' else 'missed — back to daily'}."


def _snooze(arg):
    bits = arg.split()
    if len(bits) < 2 or not bits[1].isdigit():
        return "Usage: /snooze <agent> <days>"
    until = fc.snooze(bits[0], int(bits[1]))
    return f"Snoozed {bits[0]} until {until}."


def _research(arg):
    kb = os.path.join(fc.HARMONY, "06_Research", "X_Knowledge_Base.md")
    raw_dir = f"{fc.COMMS}/research_raw"
    if not arg.strip():
        notes = fc.read(kb).count("\n### ")
        pending = len(glob.glob(f"{raw_dir}/*.json"))
        st = fc.load_state().get("agents", {}).get("research", {})
        return (f"Research KB: {notes} note(s) · {pending} pending · last run {st.get('last_run','-')}.\n"
                "Paste a tweet/thread as a normal message to save it instantly, "
                "or `/research <text or url>` to queue it.")
    os.makedirs(raw_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    url = arg.strip() if arg.strip().lower().startswith("http") else ""
    item = {"id": stamp, "url": url, "author": "", "date": datetime.date.today().isoformat(),
            "kind": "manual", "text": arg.strip()}
    fc.atomic_write(f"{raw_dir}/{stamp}.json", json.dumps(item))
    return "Queued for research — I'll distill it into your knowledge base on the next run."


def _watchlist(arg):
    wl = os.path.join(fc.HARMONY, "06_Research", "X_Watchlist.md")
    if not arg.strip():
        accts = [l.strip() for l in fc.read(wl).splitlines() if l.strip().startswith("- @")]
        return ("Watchlist accounts:\n" + "\n".join(accts[:25])) if accts else \
            "Watchlist is empty. Add one with `/watchlist @handle`."
    h = arg.strip().split()[0]
    h = "@" + h.lstrip("@")
    txt = fc.read(wl)
    if not txt:
        return "Watchlist file not found (Harmony/06_Research/X_Watchlist.md)."
    if "## Topics that matter" in txt:
        txt = txt.replace("## Topics that matter", f"- {h}\n\n## Topics that matter", 1)
    else:
        txt = txt.rstrip() + f"\n- {h}\n"
    fc.atomic_write(wl, txt)
    return f"Added {h} to your X watchlist."


def handle(text):
    text = (text or "").strip()
    if not text.startswith("/"):
        return HELP
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower().lstrip("/")
    arg = parts[1].strip() if len(parts) > 1 else ""
    if cmd == "help":
        return HELP
    if cmd == "status":
        return _status()
    if cmd == "health":
        return _health()
    if cmd == "gigs":
        g = fc.read(f"{fc.COMMS}/gigs.md").strip()
        return g[:3800] if g else "No gig scan yet - the scanner runs Mon-Sat 7:10."
    if cmd == "digest":
        return _digest()
    if cmd == "ask":
        return _ask(arg)
    if cmd == "tailor":
        return _tailor(arg)
    if cmd == "prep":
        return _prep(arg)
    if cmd == "code":
        return _code(arg)
    if cmd == "network":
        return _network(arg)
    if cmd == "queue":
        return _queue(arg)
    if cmd == "approve":
        return _move_review(arg, "approved")
    if cmd == "reject":
        return _move_review(arg, "rejected")
    if cmd == "grade":
        return _grade(arg)
    if cmd == "snooze":
        return _snooze(arg)
    if cmd == "research":
        return _research(arg)
    if cmd == "watchlist":
        return _watchlist(arg)
    return f"Unknown command /{cmd}. Try /help."


def main():
    text = " ".join(sys.argv[1:])
    reply = handle(text)
    print(reply)
    fc.log_run("commands", "ok", text.split()[0] if text else "empty")


if __name__ == "__main__":
    main()

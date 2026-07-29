#!/usr/bin/env python3
"""Chief of Staff brief - aggregates the comms blackboard AND synthesizes across it.
Generates a priorities brief from Harmony (RAG-retrieved) via the local model, runs a
cross-domain synthesis pass (the day's ONE thing + connections), then appends the
fleet's system status and every agent's needs_human[] alerts. Delivered to Telegram by
the Hermes --no-agent cron AND persisted to comms/ for the archive + dashboard."""
import os, re, glob, json, datetime, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc
import memory_index


def synthesize(signals):
    """Cross-domain synthesis (audit C2): connect the day's signals into the SINGLE
    most important focus + a few cross-domain connections. Structured JSON output;
    returns (one_thing, connections[]). Empty on any failure - the brief still works."""
    schema = {"type": "object", "properties": {
        "one_thing": {"type": "string"},
        "connections": {"type": "array", "items": {"type": "string"}}},
        "required": ["one_thing"]}
    prompt = (
        "You are Brian's chief of staff. Brian is job-hunting; income (a job) is goal #1. "
        "From the SIGNALS below, decide the SINGLE highest-leverage action Brian should take today "
        "AND why it matters most, plus up to 3 cross-domain connections worth flagging (e.g. runway "
        "vs. application pace, stress vs. missed health weeks). Be concrete and specific to the "
        "signals; do not invent numbers.\n"
        'Return JSON: {"one_thing": "<action> - because <terse reason, <=10 words>", '
        '"connections": ["short", ...]}.\n\n'
        + fc.wrap_untrusted(signals, "aggregated daily signals"))
    raw = fc.ollama_generate(prompt, fmt=schema, num_ctx=4096, temperature=0.3,
                             num_predict=300, timeout=60, retries=1, fallback="")
    try:
        d = json.loads(raw)
        return (d.get("one_thing", "").strip(),
                [c.strip() for c in (d.get("connections") or []) if c.strip()][:3])
    except Exception:
        return "", []


def build_brief():
    date_str = datetime.datetime.now().strftime("%A, %B %d, %Y")

    # Priorities blurb - context retrieved from RAG memory, truncation fallback.
    ctx = memory_index.context_for(
        "Brian's top priorities, job-hunt status, finances, health, and what needs attention today",
        fallback=fc.read_harmony("Dashboard.md")[:4000])
    prompt = (
        f"You are Brian's chief of staff. Today is {date_str}. Brian is job-hunting; income is goal #1. "
        f"From the context below, write a SHORT priorities brief in plain text, UNDER 130 words. "
        f"Use exactly these labeled lines: 'Top priority:' (usually: send 5 tailored job applications), "
        f"'Top 3:' (a numbered 1-3 list), then one encouraging sentence. No markdown headers, no preamble.\n\n"
        + fc.wrap_untrusted(ctx, "retrieved context"))
    fallback = ("Top priority: send 5 tailored job applications.\n"
                "Top 3: 1) Job apps  2) Deploy portfolio + AI Job Hunter  3) One fitness block.\n"
                "(local model unavailable - using fallback)")
    blurb = fc.ollama_generate(prompt, num_ctx=8192, temperature=0.4, num_predict=320,
                               timeout=90, retries=1, fallback=fallback)

    # Blackboard aggregation - needs_human[], minus snoozed agents, aged to cut fatigue.
    snoozed = fc.snoozed_agents()
    needs = []
    st = fc.load_state()
    for name, slc in st.get("agents", {}).items():
        if name in snoozed:
            continue
        for item in slc.get("needs_human", []) or []:
            needs.append(f"[{name}] {item}")
    needs = fc.age_needs(needs)

    # Watchdog status line
    sys_status = ""
    m = re.search(r"Status:\s*(.+)", fc.read(f"{fc.COMMS}/system_status.md"))
    if m:
        sys_status = m.group(1).strip()

    # Pending overnight reviews
    review = sorted(glob.glob(f"{fc.COMMS}/review/*.md"))
    pend = [os.path.basename(p) for p in review if "NEEDS REVIEW" in fc.read(p)]

    # Job funnel - parsed by HEADER NAME (income is goal #1; never model-reported)
    jt = fc.read_harmony("03_Career/Job_Tracker.md")
    _apps, _net, _int = (fc.tracker_cell(jt, "Applications sent"),
                         fc.tracker_cell(jt, "Networking"), fc.tracker_cell(jt, "Interviews"))
    _jp = []
    if _apps:
        _jp.append(f"{_apps[1]}/{_apps[0]} apps")
    if _net:
        _jp.append(f"{_net[1]} networking")
    if _int:
        _jp.append(f"{_int[1]} interview(s)")
    job_line = " · ".join(_jp)

    # Money & Health summaries
    def _summary(name):
        return " ".join(l for l in fc.read(f"{fc.COMMS}/{name}").splitlines()
                        if l.strip() and not l.startswith("#")).strip()
    _fin, _hea = _summary("finance.md"), _summary("health.md")

    # Cross-domain synthesis (the ONE thing)
    signals = (f"Job funnel: {job_line or 'tracker blank'}\nFinance: {_fin or 'n/a'}\n"
               f"Health: {_hea or 'n/a'}\nOpen needs: {'; '.join(needs) or 'none'}\n"
               f"Overnight drafts to review: {len(pend)}\nSystem: {sys_status or 'n/a'}")
    one_thing, connections = synthesize(signals)

    # ---- compose (alerts + the ONE thing lead; deterministic) ----
    out = [f"☀️ Daily Brief - {date_str}", ""]
    # Mission scoreboard FIRST (2026-07-11 UX): the one number that defines the week
    # (apps sent vs target) leads every brief - it was buried mid-brief on bad weeks,
    # which is exactly when it must be loudest.
    if _apps and (_apps[1] or "").strip():
        out += [f"\U0001f3af Scoreboard: {_apps[1]}/{_apps[0]} applications this week", ""]
    if needs:
        out += ["⚠️ Needs you:"] + [f"  - {n}" for n in needs] + [""]
    if pend:
        out += ["\U0001f4dd Built overnight - review & approve (comms/review/):"] + \
               [f"  - {p}" for p in pend] + [""]
    if one_thing:
        out += [f"\U0001f3af Today's ONE thing: {one_thing}", ""]
    if connections:
        out += ["\U0001f517 Connections:"] + [f"  - {c}" for c in connections] + [""]

    # Today's iCloud calendar (only real events; omitted until calendar_agent is configured)
    _cal = [l for l in fc.read(f"{fc.COMMS}/calendar.md").splitlines()
            if l.startswith("- ") and not any(s in l for s in
            ("not configured", "no events", "caldav not installed", "could not reach"))]
    if _cal:
        out += ["\U0001f4c5 Today's calendar:"] + [f"  {l}" for l in _cal[:8]] + [""]

    # Career / job-hunt - the mission (income is goal #1). Prefer the career agent's
    # richer read (apps vs target, streak, follow-ups due, stale, coaching nudge);
    # fall back to the weekly-numbers line if the career agent hasn't run.
    _career_body = [l for l in fc.read(f"{fc.COMMS}/career.md").splitlines()
                    if l.strip() and not l.startswith("#")]
    if _career_body:
        out += ["\U0001f9ed Job hunt:"] + [(l if l.startswith("  ") else "  " + l) for l in _career_body[:9]] + [""]
    elif job_line:
        out += [f"\U0001f9ed Job hunt this week: {job_line}", ""]

    _scout = [l for l in fc.read(f"{fc.COMMS}/scout.md").splitlines() if l.startswith("- ")][:5]
    if _scout:
        out += ["\U0001f50d Scout - fresh listings:"] + [f"  {l}" for l in _scout] + [""]

    out += [blurb, "", f"\U0001f527 System: {sys_status or 'no watchdog report yet'}"]
    try:
        r = json.load(open(f"{fc.COMMS}/resource_status.json"))
        out.append(f"\U0001f4be RAM {r['ram_free_gb']} GB free ({r['ram_pct']}% used), commit {r['commit_pct']}%")
    except Exception:
        pass
    if _fin or _hea:
        out += ["", "\U0001f4b0 Money & Health:"]
        if _fin:
            out.append(f"  Finance: {_fin}")
        if _hea:
            out.append(f"  Health: {_hea}")

    # Research: new insights saved to the X knowledge base in the last 7 days
    kb = fc.read(os.path.join(fc.HARMONY, "06_Research", "X_Knowledge_Base.md"))
    if kb:
        week_ago = datetime.date.today() - datetime.timedelta(days=7)
        recent = []
        for b in kb.split("\n### ")[1:]:
            title = b.splitlines()[0].strip()
            m = re.search(r"_\(saved (\d{4}-\d{2}-\d{2})\)_", b)
            if m:
                try:
                    d = datetime.datetime.strptime(m.group(1), "%Y-%m-%d").date()
                    if d >= week_ago:
                        recent.append((d, title))
                except Exception:
                    pass
        if recent:
            recent.sort(reverse=True)
            out += ["", f"\U0001f4da Research: {len(recent)} new insight(s) saved this week"]
            out += [f"  - {t}" for _, t in recent[:2]]

    qlines = [l.strip() for l in fc.read(f"{fc.COMMS}/recall.md").splitlines() if re.match(r"\s*\d", l)][:3]
    if qlines:
        out += ["", "\U0001f9e0 Recall (test yourself):"] + [f"  {l}" for l in qlines]

    # Confidence flag (#15): name where the brief is running on blank trackers, so Brian
    # knows which guidance is data-backed vs. generic. Honest > confidently-wrong.
    thin = []
    if not job_line and not _career_body:
        thin.append("Job_Tracker")
    if not _fin or any(w in _fin.lower() for w in ("blank", "offline", "n/a")):
        thin.append("Finance")
    if not _hea or any(w in _hea.lower() for w in ("blank", "offline", "n/a")):
        thin.append("Health")
    if thin:
        verb = "is" if len(thin) == 1 else "are"
        out += ["", f"ℹ️ Low-data note: {', '.join(thin)} {verb} on blank/empty trackers - "
                    f"fill for sharper guidance."]

    return "\n".join(out), len(needs), len(pend)


def main():
    # The brief is delivered as this script's stdout. If it ever prints nothing,
    # Hermes treats it as [SILENT] and skips delivery -- so the morning message
    # silently vanishes. Guarantee we ALWAYS emit a non-empty brief.
    stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    text = ""
    try:
        text, n_needs, n_pend = build_brief()
        fc.atomic_write(f"{fc.COMMS}/daily_brief.md", text + "\n")
        fc.atomic_write(f"{fc.COMMS}/briefs/{stamp}.md", text + "\n")
        fc.log_run("chief_of_staff", "ok", f"{n_needs} needs, {n_pend} review")
    except Exception as e:
        # Fall back to a minimal but real brief rather than going dark.
        text = (f"☀️ Daily Brief - {datetime.date.today():%A, %B %d, %Y}\n\n"
                f"⚠️ Brief generation hit an error and fell back to a minimal view.\n"
                f"   {type(e).__name__}: {str(e)[:160]}\n"
                f"The fleet is alive (you're getting this message). Full status: /fleet")
        try:
            fc.log_run("chief_of_staff", "error", f"{type(e).__name__}: {str(e)[:160]}")
        except Exception:
            pass
    if not text or not text.strip():
        text = (f"☀️ Daily Brief - {datetime.date.today():%A, %B %d, %Y}\n"
                f"(Brief came back empty, but the fleet is alive. Try /fleet.)")
    # Deliver DIRECTLY via the Telegram Bot API (update-proof + UTF-8, so emoji work
    # and it doesn't depend on Hermes's cron delivery, which a 2026-06-23 Hermes update
    # broke twice - decode-to-[SILENT] then a missing-token send error). This cron is
    # set to --deliver local so Hermes won't double-send; print() just feeds logs/dash.
    fc.telegram_send(text, urgent=True)
    # iMessage delivery is done by the GATEWAY (it owns the Photon sidecar; a cron process
    # can't spawn it). The daily-brief cron's --deliver target is set to photon, so the
    # gateway sends this same brief to Brian's iPhone. Telegram stays on the direct path above.
    print(fc.ascii_fold(text))
    # Daily heartbeat to the external dead-man's-switch (no-op until configured).
    fc.ping_healthcheck()


if __name__ == "__main__":
    main()

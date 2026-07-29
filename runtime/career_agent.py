#!/usr/bin/env python3
"""Career / job-hunt agent - the mission engine (goal #1: income).

Reads Harmony/03_Career/Job_Tracker.md (real format: weekly-numbers table +
pipeline table; Brian's goal = 5 tailored applications/day). DETERMINISTICALLY
parses the funnel so the morning brief can hold Brian accountable:
  - applications logged this week vs. target (25/wk = 5/day)
  - current application streak (consecutive days with >=1 app)
  - follow-ups DUE today (follow-up date <= today, still in early stages)
  - STALE applications (applied >7 days ago, still "Applied", no response)
  - open pipeline by stage + simple conversion read

SAFE: never invents numbers - only counts what's logged. If the tracker is the
blank template it nudges the ONE next action (apply to 5 from the target board).
Draft-only: it never applies to anything. Producer on the blackboard:
writes comms/career.md + a state slice; the daily brief aggregates it.
"""
import os, sys, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

TRACKER = "03_Career/Job_Tracker.md"
EARLY_STAGES = ("applied", "responded", "screen")     # still need a follow-up
WEEK_TARGET = 25                                       # 5/day x 5 days
STALE_DAYS = 7


def _parse_date(s):
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%b %d", "%B %d"):
        try:
            d = datetime.datetime.strptime(s, fmt).date()
            if d.year == 1900:                         # %b %d has no year -> assume this year
                d = d.replace(year=datetime.date.today().year)
            return d
        except Exception:
            continue
    return None


def _pipeline_rows(md):
    """Return list of dicts for real (non-empty) pipeline rows."""
    rows, in_pipe = [], False
    for ln in md.splitlines():
        if ln.strip().lower().startswith("## pipeline"):
            in_pipe = True
            continue
        if in_pipe and ln.startswith("## "):           # next section ends the table
            break
        if in_pipe and ln.strip().startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) < 6:
                continue
            head = cells[0].lower()
            # skip header / separator / fully-blank rows
            if head == "date":
                continue
            if set("".join(cells)) <= set("-: "):
                continue
            if not (cells[0] or cells[1] or cells[2]):
                continue
            rows.append({
                "date": _parse_date(cells[0]), "company": cells[1], "role": cells[2],
                "status": (cells[4] if len(cells) > 4 else "").lower(),
                "followup": _parse_date(cells[6]) if len(cells) > 6 else None,
            })
    return rows


def _streak(dates):
    """Consecutive days (ending today or yesterday) with >=1 application."""
    days = {d for d in dates if d}
    if not days:
        return 0
    today = datetime.date.today()
    start = today if today in days else (today - datetime.timedelta(days=1))
    if start not in days:
        return 0
    n, cur = 0, start
    while cur in days:
        n += 1
        cur -= datetime.timedelta(days=1)
    return n


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:40] or "role"


def _draft_followups(due, pitch):
    """Auto-draft a follow-up message for each DUE application into the approval queue
    (comms/review/), marked NEEDS REVIEW so it shows in the brief and can be approved
    via /approvedraft. Draft-only: never sends. Deduped by file; capped at 3/run."""
    made = []
    rdir = os.path.join(fc.COMMS, "review")
    os.makedirs(rdir, exist_ok=True)
    for r in due[:3]:
        path = os.path.join(rdir, f"followup-{_slug(r['company'] + '-' + r['role'])}.md")
        if os.path.exists(path):
            continue
        prompt = (
            "Write a SHORT, warm, professional job-application follow-up (60-80 words, first "
            "person as Brian, no subject line). Reference the company and role, reaffirm genuine "
            "interest, offer to share more. Plain text, ready to paste. Do NOT invent details.\n"
            f"COMPANY: {r['company']}\nROLE: {r['role']}\nBRIAN'S PITCH: {pitch}")
        msg = fc.ollama_generate(prompt, num_ctx=4096, temperature=0.5, num_predict=180,
                                 timeout=90, retries=1, fallback="")
        if not msg.strip():
            continue
        fc.atomic_write(path,
            f"# Review: Follow-up - {r['company']} {r['role']}\n"
            f"STATUS: NEEDS REVIEW - drafted {datetime.date.today()} (applied {r['date']})\n\n"
            f"## Draft follow-up (approve, then send it yourself)\n{msg.strip()}\n")
        made.append(f"{r['company']} {r['role']}".strip())
    return made


def main():
    md = fc.read_harmony(TRACKER) or ""
    rows = _pipeline_rows(md)
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())

    this_week = [r for r in rows if r["date"] and r["date"] >= monday]
    streak = _streak([r["date"] for r in rows])
    due = [r for r in rows if r["followup"] and r["followup"] <= today
           and any(s in r["status"] for s in EARLY_STAGES)]
    stale = [r for r in rows if r["date"] and (today - r["date"]).days >= STALE_DAYS
             and "applied" in r["status"]
             and not any(s in r["status"] for s in ("respond", "screen", "interview", "offer", "reject"))]
    interviews = [r for r in rows if "interview" in r["status"] or "offer" in r["status"]]
    responses = [r for r in rows if any(s in r["status"] for s in ("respond", "screen", "interview", "offer"))]

    # Networking touches this week (#26) from the /network log.
    net_week = 0
    for ln in fc.read(f"{fc.COMMS}/networking.md").splitlines():
        nm = re.match(r"-\s*(\d{4}-\d{2}-\d{2})", ln.strip())
        if nm:
            try:
                if datetime.datetime.strptime(nm.group(1), "%Y-%m-%d").date() >= monday:
                    net_week += 1
            except Exception:
                pass

    # Auto-draft follow-ups for due applications into the approval queue (#21).
    pm = re.search(r"pitch.*?\n>\s*_?(.+)", md, re.I | re.S)
    pitch = (pm.group(1).strip(" _>") if pm else
             "Self-taught full-stack / AI-app developer who ships real React/TS, Next.js, Python projects.")[:300]
    drafted = _draft_followups(due, pitch) if due else []

    # Deterministic headline (never invented)
    n_week = len(this_week)
    bits = [f"{n_week}/{WEEK_TARGET} apps this week"]
    if streak:
        bits.append(f"{streak}-day streak")
    if net_week:
        bits.append(f"{net_week} networking")
    if due:
        bits.append(f"{len(due)} follow-up(s) due")
    if stale:
        bits.append(f"{len(stale)} stale (>{STALE_DAYS}d, no reply)")
    if interviews:
        bits.append(f"{len(interviews)} in interview/offer")
    headline = " · ".join(bits)

    # One LLM nudge: the single highest-leverage job-hunt action today.
    due_txt = "; ".join(f"{r['company']} {r['role']}".strip() for r in due[:3]) or "none"
    stale_txt = "; ".join(f"{r['company']} {r['role']}".strip() for r in stale[:3]) or "none"
    prompt = (
        "You are Brian's job-hunt coach writing ONE line (under 45 words, plain text, no preamble) "
        "for his morning brief. Goal: 5 tailored applications/day to React/TypeScript, Next.js, Python, "
        "and AI-application engineer roles (Wellfound, YC Work-at-a-Startup, LinkedIn). Targeting beats "
        "volume - tailored, not spray. Given today's numbers, name the SINGLE highest-leverage next action. "
        f"If apps this week ({n_week}) is below target, push to apply. If follow-ups are due ({due_txt}), "
        f"prioritize the nudge. If applications are stale ({stale_txt}), suggest a follow-up or moving on.\n"
        f"NUMBERS: {headline}."
    )
    nudge = fc.ollama_generate(prompt, num_ctx=4096, temperature=0.4, num_predict=110,
                               timeout=90, retries=1,
                               fallback="Apply to 5 fitting roles on Wellfound + log them; send any due follow-ups.")

    stamp = today.strftime("%Y-%m-%d")
    lines = [f"# Career / Job Hunt - {stamp}", "", f"**{headline}**", "", nudge.strip()]
    if due:
        lines += ["", "Follow-ups due:"] + [f"  - {r['company']} {r['role']} (applied {r['date']})".rstrip() for r in due[:5]]
    if stale:
        lines += ["", "Going stale (consider a nudge or move on):"] + [f"  - {r['company']} {r['role']}".rstrip() for r in stale[:5]]
    fc.atomic_write(f"{fc.COMMS}/career.md", "\n".join(lines) + "\n")

    needs = []
    if drafted:
        needs.append(f"{len(drafted)} follow-up draft(s) ready to review (comms/review/)")
    elif due:
        needs.append(f"{len(due)} follow-up(s) due")
    if n_week < WEEK_TARGET:
        needs.append(f"{WEEK_TARGET - n_week} more apps to hit weekly target")
    fc.state_update("career", {"last_run": stamp, "status": "ok", "summary": headline[:90],
                               "apps_week": n_week, "streak": streak, "due": len(due),
                               "stale": len(stale), "interviews": len(interviews),
                               "responses": len(responses), "networking": net_week, "needs_human": needs})
    print(f"Career: {headline}\n{nudge.strip()}")
    fc.log_run("career", "ok", headline)


if __name__ == "__main__":
    main()

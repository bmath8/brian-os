#!/usr/bin/env python3
"""Outcome learner - closes the loop the career agent opens (roadmap Tier-4 #15).

The career agent counts activity (apps sent); this agent measures what WORKED:
which kinds of applications actually got responses. Deterministic parse of
Harmony/03_Career/Job_Tracker.md pipeline rows -> response/interview rate by
role-keyword bucket, by source (if a source column exists), and by day-of-week,
then ONE local-LLM recommendation. Evidence-based tailoring instead of vibes.

SAFE: counts only what's logged; never invents numbers; draft-only producer
(writes comms/outcomes.md + a state slice; weekly review + brief read it).
Runs weekly (Sun 16:50) - outcomes move slowly.
"""
import os, sys, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc
from career_agent import _pipeline_rows

RESPONDED = ("respond", "screen", "interview", "offer")
BUCKETS = {
    "AI/LLM": ("ai", "llm", "ml", "machine learning", "agent", "prompt"),
    "Frontend/React": ("react", "frontend", "front-end", "next", "typescript", "ui"),
    "Full-stack": ("full stack", "fullstack", "full-stack"),
    "Python/Backend": ("python", "backend", "back-end", "django", "fastapi", "node"),
    "Automation": ("automation", "integration", "workflow", "rpa"),
}


def _bucket(role):
    r = (role or "").lower()
    for name, kws in BUCKETS.items():
        if any(k in r for k in kws):
            return name
    return "Other"


def _rate(rows):
    n = len(rows)
    hits = sum(1 for r in rows if any(s in r["status"] for s in RESPONDED))
    return n, hits, (100.0 * hits / n if n else 0.0)


def main():
    rows = [r for r in _pipeline_rows(fc.read_harmony("03_Career/Job_Tracker.md") or "")
            if r.get("date")]
    stamp = datetime.date.today().isoformat()
    if len(rows) < 5:
        msg = (f"# Application outcomes - {stamp}\n\nOnly {len(rows)} logged application(s) - "
               f"need ~5+ before patterns mean anything. Keep logging every app in Job_Tracker; "
               f"this report sharpens automatically.\n")
        fc.atomic_write(f"{fc.COMMS}/outcomes.md", msg)
        fc.state_update("outcomes", {"last_run": stamp, "status": "ok",
                                     "summary": f"{len(rows)} apps logged - too few for patterns",
                                     "needs_human": []})
        fc.log_run("outcome_learner", "ok", f"{len(rows)} rows (below threshold)")
        print(msg)
        return

    total_n, total_hits, total_rate = _rate(rows)
    lines = [f"# Application outcomes - {stamp}", "",
             f"**Overall: {total_hits}/{total_n} got a response ({total_rate:.0f}%)**", "",
             "## By role type"]
    by_bucket = {}
    for r in rows:
        by_bucket.setdefault(_bucket(r["role"]), []).append(r)
    best = None
    for name, rs in sorted(by_bucket.items(), key=lambda kv: -_rate(kv[1])[2]):
        n, hits, rate = _rate(rs)
        lines.append(f"- {name}: {hits}/{n} responses ({rate:.0f}%)")
        if best is None and n >= 3:
            best = (name, rate)

    # Day-of-week effect (applications sent Mon-Tue historically outperform)
    lines += ["", "## By day applied"]
    by_dow = {}
    for r in rows:
        by_dow.setdefault(r["date"].strftime("%a"), []).append(r)
    for dow in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
        if dow in by_dow:
            n, hits, rate = _rate(by_dow[dow])
            lines.append(f"- {dow}: {hits}/{n} ({rate:.0f}%)")

    # ONE evidence-based recommendation (local, free, no-op-safe)
    rec = fc.ollama_generate(
        "You are a job-search analyst. From the response-rate DATA below, write ONE specific, "
        "actionable recommendation (<=35 words, plain text) for where Brian should focus next "
        "week's applications. Cite the numbers. Never invent data.\n\nDATA:\n" +
        "\n".join(lines), num_ctx=4096, temperature=0.3, num_predict=90,
        timeout=90, retries=1, fallback="")
    if rec.strip():
        lines += ["", f"**Recommendation:** {rec.strip()}"]

    fc.atomic_write(f"{fc.COMMS}/outcomes.md", "\n".join(lines) + "\n")
    summary = f"{total_rate:.0f}% response rate ({total_hits}/{total_n})"
    if best:
        summary += f" · best: {best[0]} {best[1]:.0f}%"
    fc.state_update("outcomes", {"last_run": stamp, "status": "ok",
                                 "summary": summary[:90], "needs_human": []})
    fc.log_run("outcome_learner", "ok", summary)
    print("\n".join(lines))


if __name__ == "__main__":
    main()

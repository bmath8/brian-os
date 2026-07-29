#!/usr/bin/env python3
"""Weekly review agent - does Brian's weekly reflection FOR him, from the data.
Compiles the week's fleet activity (run_log) + job funnel (Job_Tracker, deterministic) +
latest finance/health into a short review: what happened, an honest funnel read, and ONE
change for next week. Writes the full review into Harmony 02_Weekly_Reviews and delivers a
short version to Telegram. Cron: Sunday 17:00.
"""
import os, sys, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc


def main():
    jt = fc.read_harmony("03_Career/Job_Tracker.md")
    funnel = {k: fc.tracker_cell(jt, k) for k in
              ("Applications sent", "Networking", "Follow-ups", "Interviews")}
    funnel_line = " · ".join(f"{k.split()[0]}: {v[1]}/{v[0]}" for k, v in funnel.items() if v)

    # Fleet activity + health this week from run_log (last 7 days) - the system report (#55).
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    runs = errors = 0
    for ln in fc.read(fc.RUN_LOG).splitlines():
        m = re.match(r"(\d{4}-\d{2}-\d{2})", ln.strip())
        if m:
            try:
                if datetime.datetime.strptime(m.group(1), "%Y-%m-%d") >= week_ago:
                    runs += 1
                    if "| error" in ln or "| alert" in ln or "fail" in ln.lower():
                        errors += 1
            except Exception:
                pass

    # Job-hunt scorecard from the career agent's state (#27): apps/responses/interviews + conversion.
    cst = fc.load_state().get("agents", {}).get("career", {})
    apps_wk, resp, ints = cst.get("apps_week", 0), cst.get("responses", 0), cst.get("interviews", 0)
    streak = cst.get("streak", 0)
    conv = f"{round(100 * resp / apps_wk)}% response rate" if apps_wk else "no apps logged yet"
    scorecard = f"Apps {apps_wk} · responses {resp} · interviews {ints} · {conv} · {streak}-day streak"

    # Trajectory self-eval (2026-07-06): the fleet already logs machine-readable runs;
    # surface fail% / escalation% per agent so drift shows up in the Sunday review.
    tstats = fc.trajectory_stats(limit=500)
    tline = ""
    if tstats.get("n"):
        worst = sorted(tstats["by_agent"].items(),
                       key=lambda kv: kv[1]["fails"] / max(kv[1]["runs"], 1), reverse=True)[:3]
        tline = " · ".join(f"{a}: {b['fails']}/{b['runs']} fail, {b['escalated']} esc"
                           for a, b in worst)

    fin = fc.read(f"{fc.COMMS}/finance.md")
    hea = fc.read(f"{fc.COMMS}/health.md")
    src = (f"JOB FUNNEL (this week, real numbers): {funnel_line or 'tracker blank'}\n"
           f"JOB-HUNT SCORECARD: {scorecard}\n"
           f"FLEET HEALTH: {runs} agent runs logged in the last 7 days, {errors} error/alert run(s).\n"
           + (f"AGENT TRAJECTORIES (worst first): {tline}\n" if tline else "")
           + f"FINANCE NOTE: {fin[:300]}\nHEALTH NOTE: {hea[:300]}")

    prompt = (
        "You are Brian's chief of staff writing his WEEKLY review. Brian is job-hunting; income is goal #1. "
        "Using the data below, write a short, honest, encouraging weekly review in plain text (UNDER 160 words): "
        "1) a one-line read on the job funnel (don't restate every number, interpret it), "
        "2) what the system/week looked like, 3) the SINGLE most important change for next week, "
        "4) one encouraging sentence. Don't invent numbers beyond what's given. No markdown headers.\n\n" + src)
    review = fc.ollama_generate(prompt, num_ctx=8192, temperature=0.5, num_predict=400,
                                timeout=120, retries=1, fallback="(weekly review offline this run)")

    stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    full = (f"# Weekly Review - week ending {stamp}\n\n"
            f"**Job funnel:** {funnel_line or 'tracker still blank - fill in this week’s numbers'}\n"
            f"**Scorecard:** {scorecard}\n"
            f"**Fleet:** {runs} agent runs ({errors} error/alert) in the last 7 days.\n"
            + (f"**Trajectories:** {tline}\n" if tline else "")
            + f"\n{review}\n")

    wk_dir = os.path.join(fc.HARMONY, "02_Weekly_Reviews")
    try:
        os.makedirs(wk_dir, exist_ok=True)
        fc.atomic_write(f"{wk_dir}/Weekly_Review_{stamp}.md", full)
        where = "saved to Harmony/02_Weekly_Reviews"
    except Exception as e:
        where = f"(could not write to Harmony: {e})"

    _msg = f"\U0001f4c5 Weekly Review - {stamp}\nJob funnel: {funnel_line or 'tracker blank'}\n\n{review}\n\n({where})"
    fc.telegram_send(_msg, urgent=True)            # direct API (update-proof)
    print(fc.ascii_fold(_msg))
    fc.state_update("weekly_review", {"last_run": stamp, "status": "ok",
                                      "summary": "weekly review generated", "needs_human": []})
    fc.log_run("weekly_review", "ok", "review generated")


if __name__ == "__main__":
    main()

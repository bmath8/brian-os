#!/usr/bin/env python3
"""Fleet CEO report - monthly one-pager (roadmap Tier-4 #17).

Brian reads this like an investor update for his own life: what the fleet cost
(still $0?), what it shipped, where it failed, and next month's bets. All
numbers are DETERMINISTIC (trajectory.jsonl, run_log, review outcomes, git log);
one local-LLM paragraph turns them into a readable narrative. Sent to Telegram
on the 1st + persisted to comms/ceo_report.md.
"""
import os, sys, glob, datetime, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc


def main():
    today = datetime.date.today()
    month = (today.replace(day=1) - datetime.timedelta(days=1)).strftime("%B %Y")
    stats = fc.trajectory_stats(limit=2000)

    runs = sum(b["runs"] for b in stats["by_agent"].values())
    fails = sum(b["fails"] for b in stats["by_agent"].values())
    esc = sum(b["escalated"] for b in stats["by_agent"].values())
    if runs == 0:
        # trajectory.jsonl only logs router/eval runs today - fall back to the cron
        # run ledger so the report reflects the REAL fleet activity.
        cutoff = (today - datetime.timedelta(days=30)).isoformat()
        for ln in fc.read(fc.RUN_LOG).splitlines():
            bits = [b.strip() for b in ln.split("|")]
            if len(bits) >= 4 and bits[0][:10] >= cutoff:
                runs += 1
                if bits[3] not in ("ok", "alert"):
                    fails += 1
    worst = sorted(((n, b) for n, b in stats["by_agent"].items() if b["runs"] >= 3),
                   key=lambda kv: -(kv[1]["fails"] / kv[1]["runs"]))[:3]

    approved = len(glob.glob(f"{fc.COMMS}/review/approved/*.md"))
    rejected = len(glob.glob(f"{fc.COMMS}/review/rejected/*.md"))
    pending = len(glob.glob(f"{fc.COMMS}/review/*.md"))

    try:
        commits = subprocess.run(
            ["git", "-C", fc.ROOT, "log", "--oneline", "--since=30.days"],
            capture_output=True, text=True, timeout=30).stdout.strip().splitlines()
    except Exception:
        commits = []

    career = fc.load_state().get("agents", {}).get("career", {})
    outcomes = fc.load_state().get("agents", {}).get("outcomes", {})

    facts = [
        f"Period: last 30 days (through {today.isoformat()})",
        f"Cost: $0 marginal (all local models; subscriptions only)",
        f"Agent runs: {runs} · failures: {fails} ({100*fails/max(runs,1):.1f}%) · cloud escalations: {esc}",
        f"Drafts: {approved} approved · {rejected} rejected · {pending} pending review",
        f"Job hunt: {career.get('summary', 'no career data')}",
        f"Outcomes: {outcomes.get('summary', 'not yet measured')}",
        f"Fleet changes shipped: {len(commits)} commits",
    ]
    if worst:
        facts.append("Weakest agents: " + "; ".join(
            f"{n} {100*b['fails']/b['runs']:.0f}% fail" for n, b in worst))

    narrative = fc.ollama_generate(
        "You are the COO writing a monthly one-paragraph CEO update (<=90 words, plain "
        "text, direct, no fluff) about a personal AI-agent fleet, from the FACTS below. "
        "Lead with the mission (income/job hunt), then reliability, then ONE clear "
        "recommendation for next month. Never invent numbers.\n\nFACTS:\n" + "\n".join(facts),
        num_ctx=4096, temperature=0.4, num_predict=200, timeout=90, retries=1, fallback="")

    lines = [f"\U0001f4c8 Fleet CEO report - {month}", ""]
    if narrative.strip():
        lines += [narrative.strip(), ""]
    lines += ["The numbers:"] + [f"  - {f}" for f in facts]
    if commits:
        lines += ["", "Shipped (last 5):"] + [f"  - {c[:80]}" for c in commits[:5]]
    text = "\n".join(lines)

    fc.atomic_write(f"{fc.COMMS}/ceo_report.md", text + "\n")
    fc.state_update("ceo_report", {"last_run": today.isoformat(), "status": "ok",
                                   "summary": f"{runs} runs, {100*fails/max(runs,1):.1f}% fail, {approved} approved",
                                   "needs_human": []})
    fc.telegram_send(text)
    fc.log_run("ceo_report", "ok", f"{runs} runs analyzed")
    print(fc.ascii_fold(text))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Finance agent - reads Brian's Harmony finance + credit trackers and writes a short
status line for the morning brief. Goals: income (job first) + rebuild credit.

SAFE: never invents numbers. If the tracker is still a blank template, it nudges the ONE
most useful thing to fill in. Producer on the blackboard: writes comms/finance.md +
state.json slice; the daily brief aggregates it.
"""
import os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc


def main():
    fin = fc.read_harmony("05_Finance/Finance_Tracker_and_Credit_Plan.md")
    credit = fc.read_harmony("05_Finance/Credit_Rebuild_Action_Plan.md")
    src = (fin + "\n\n--- CREDIT PLAN ---\n" + credit)[:3500]

    prompt = (
        "You are Brian's finance agent writing ONE line for his morning brief. Brian's goals: "
        "income (get a job first) and rebuild credit. From the tracker below write UNDER 55 words, "
        "plain text, no headers, no preamble. RULES: never invent numbers - only use figures present "
        "in the tracker. If ANY real numbers exist (cash, ETH, etc.), STATE the current liquid position "
        "first (total + its parts). Then name the single most useful next step: if monthly expenses are "
        "still blank, that's what's needed to compute runway; otherwise give months-of-runway + the next "
        "credit-rebuild action.\n\nTRACKER:\n" + src)
    out = fc.ollama_generate(prompt, num_ctx=8192, temperature=0.3, num_predict=160,
                             timeout=90, retries=1, fallback="(finance agent offline this run)")

    stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    fc.atomic_write(f"{fc.COMMS}/finance.md", f"# Finance - {stamp}\n{out}\n")
    fc.state_update("finance", {"last_run": stamp, "status": "ok",
                                "summary": out[:80], "needs_human": []})
    print(f"Finance: {out}")
    fc.log_run("finance", "ok", "status refreshed")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Health agent - reads Brian's Harmony health tracker and writes a short status line for
the morning brief. Goal: sustainable body composition, consistency over intensity.

SAFE: never invents data, gives no medical advice. If the tracker is a blank template, it
nudges the ONE next thing to log. Producer on the blackboard.
"""
import os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc


def main():
    src = fc.read_harmony("04_Health/Health_Baseline_and_Tracker.md")[:3500]

    prompt = (
        "You are Brian's health agent writing ONE line for his morning brief. Goal: sustainable body "
        "composition; the plan is strength 3x/week, 8k steps, protein, 7-8h sleep. From the tracker "
        "below write UNDER 45 words, plain text, no headers, encouraging but honest.\n"
        "CRITICAL: the Weekly log table is likely EMPTY (blank cells, just '/3' and '/7' placeholders). "
        "If NO weeks are actually logged, you MUST NOT claim any workouts, steps, protein, or sleep "
        "happened - that would be fabrication. Instead say the log is empty and nudge the ONE simplest "
        "thing to start logging this week. Only describe real adherence if the table contains real "
        "filled-in numbers. No medical advice.\n\nTRACKER:\n" + src)
    out = fc.ollama_generate(prompt, num_ctx=8192, temperature=0.4, num_predict=140,
                             timeout=90, retries=1, fallback="(health agent offline this run)")

    stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    fc.atomic_write(f"{fc.COMMS}/health.md", f"# Health - {stamp}\n{out}\n")
    fc.state_update("health", {"last_run": stamp, "status": "ok",
                               "summary": out[:80], "needs_human": []})
    print(f"Health: {out}")
    fc.log_run("health", "ok", "status refreshed")


if __name__ == "__main__":
    main()

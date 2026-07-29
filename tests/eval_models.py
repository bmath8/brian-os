#!/usr/bin/env python3
"""eval_models.py - compare two local models on the fleet's REAL tasks, head to head.
Not a unit test (won't be picked up by `unittest discover`); a manual harness for the
monthly model review so "is the new model better?" is a measurement, not a vibe.

Usage:  python3 tests/eval_models.py qwen3:8b qwen3:14b
Prints latency + output for each task/model so you can eyeball quality + speed.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))
import fleet_common as fc

TASKS = [
    ("brief", "Write a 2-line morning priorities note for a job-seeker. Plain text."),
    ("summary", "Summarize in one sentence: the fleet self-heals Ollama and the gateway, "
                "runs 10 local agents on a schedule, and delivers a morning brief to Telegram."),
    ("recall", "Write exactly 3 short active-recall questions about local LLM ops. Numbered 1-3."),
    ("draft", "Draft a 3-sentence outreach message to a hiring manager for a full-stack role."),
    ("classify", "Classify the sentiment (positive/neutral/negative): 'The gateway crashed again.'"),
]


def run(model, prompt):
    t0 = time.time()
    out = fc.ollama_generate(prompt, model=model, num_ctx=4096, num_predict=200,
                             timeout=120, retries=0, fallback="(failed)")
    return round(time.time() - t0, 1), out


def main():
    models = sys.argv[1:3] or [fc.SMALL_MODEL, fc.BIG_MODEL]
    print(f"Eval: {models[0]}  vs  {models[1]}\n" + "=" * 60)
    for name, prompt in TASKS:
        print(f"\n### {name.upper()}\n{prompt}")
        for m in models:
            secs, out = run(m, prompt)
            print(f"\n-- {m}  ({secs}s) --\n{out.strip()[:600]}")
        print("-" * 60)


if __name__ == "__main__":
    main()

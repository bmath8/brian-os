#!/usr/bin/env python3
"""feedback.py - capture Brian's approve/reject decisions on overnight drafts (audit D3).
He signals by moving a file from comms/review/ into review/approved/ or review/rejected/.
This records each outcome once to comms/.feedback/outcomes.jsonl and writes a short
summary (comms/feedback.md). The overnight worker reads review/approved/ as exemplars,
so the loop closes: your taste shapes future drafts.

Run (cron, e.g. with the weekly review):  python3 feedback.py
"""
import os, sys, json, glob, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

REVIEW = f"{fc.COMMS}/review"
FB_DIR = f"{fc.COMMS}/.feedback"
LOG = f"{FB_DIR}/outcomes.jsonl"


def _seen():
    s = set()
    for ln in fc.read(LOG).splitlines():
        try:
            s.add(json.loads(ln)["file"])
        except Exception:
            pass
    return s


def main():
    os.makedirs(FB_DIR, exist_ok=True)
    seen = _seen()
    new = 0
    for outcome in ("approved", "rejected"):
        for p in glob.glob(f"{REVIEW}/{outcome}/*.md"):
            name = os.path.basename(p)
            key = f"{outcome}/{name}"
            if key in seen:
                continue
            rec = {"file": key, "outcome": outcome,
                   "ts": datetime.datetime.now().isoformat(timespec="seconds")}
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            new += 1

    appr = sum(1 for ln in fc.read(LOG).splitlines() if '"approved"' in ln)
    rej = sum(1 for ln in fc.read(LOG).splitlines() if '"rejected"' in ln)
    total = appr + rej
    rate = f"{100*appr//total}%" if total else "n/a"
    md = (f"# Draft Feedback - {fc.now()}\n\n"
          f"Approved: {appr} · Rejected: {rej} · Approval rate: {rate}\n"
          f"New this run: {new}\n\n"
          f"_Move a file from comms/review/ into review/approved/ or review/rejected/ to log it. "
          f"The overnight worker few-shots from review/approved/._\n")
    fc.atomic_write(f"{fc.COMMS}/feedback.md", md)
    print(md)
    fc.log_run("feedback", "ok", f"{new} new, {appr} appr / {rej} rej")


if __name__ == "__main__":
    main()

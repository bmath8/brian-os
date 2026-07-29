#!/usr/bin/env python3
"""Inbox watcher (#33) - surfaces new files dropped into Harmony/00_Inbox so they
don't get lost. Lists files added/changed in the last ~26h, writes comms/inbox.md
and a state slice; the brief shows them under "Needs you". READ-ONLY by design: it
never opens, moves, or deletes files - it just tells Brian what landed, so he (or a
future ingest step) can act on it. Cron: daily, just before the brief.
"""
import os, sys, time, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

INBOX = os.path.join(fc.HARMONY, "00_Inbox")


def main():
    cutoff = time.time() - 26 * 3600
    recent = []
    try:
        for name in os.listdir(INBOX):
            p = os.path.join(INBOX, name)
            if os.path.isfile(p) and not name.startswith(".") and os.path.getmtime(p) >= cutoff:
                recent.append(name)
    except Exception:
        pass
    recent.sort()

    stamp = datetime.date.today().isoformat()
    lines = [f"# Inbox - {stamp}"]
    lines += [f"- {n}" for n in recent] if recent else ["- (nothing new in the last day)"]
    fc.atomic_write(f"{fc.COMMS}/inbox.md", "\n".join(lines) + "\n")

    needs = [f"{len(recent)} new file(s) in Harmony/00_Inbox to process"] if recent else []
    fc.state_update("inbox", {"last_run": stamp, "status": "ok",
                              "summary": f"{len(recent)} new file(s)", "needs_human": needs})
    print(f"Inbox: {len(recent)} new file(s)")
    fc.log_run("inbox", "ok", f"{len(recent)} new")


if __name__ == "__main__":
    main()

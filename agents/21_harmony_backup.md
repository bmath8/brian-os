# Agent 21 — Harmony Backup
_Backup of the Harmony second-brain so nothing is lost to a disk/OneDrive failure._

- **Owns:** the durable copy of `C:\Users\mathe\OneDrive\Desktop\Harmony`.
- **Why it exists:** Harmony is the single source of Brian's trackers (finance, health, career, research). One wipe = years of context gone. _Solves:_ catastrophic loss.
- **Cadence:** daily 1:30 AM (cron `harmony-backup`, `no_agent` script `backup_harmony.py`).
- **Tier/model:** no model — deterministic `robocopy` to a local backup root.
- **Deliver:** writes `comms/.last_backup` stamp (used by the watchdog to detect "stale" falsely).

## What it does (as implemented)
- Robocopies Harmony → backup root (mirror, restarts/resumes safe).
- Stamps `comms/.last_backup` with the run time so the watchdog's "backup stale?" check reads mtime vs job-ran (the old alert was a false positive from this confusion — fixed).

## Output (writes)
- Backup mirror at the configured root.
- `comms/.last_backup`.

## Hard rule
Copy-only. Never deletes from the source.

## Done-when
Mirror current; `.last_backup` fresh; watchdog's stale check agrees.

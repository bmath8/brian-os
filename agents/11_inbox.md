# Agent 11 — Inbox
_Surfaces new files dropped into Harmony's 00_Inbox._

- **Owns:** the "Inbox" triage nudge in the brief.
- **Why it exists:** things land in Harmony's inbox and get forgotten. _Solves:_ orphaned notes/files.
- **Cadence:** daily, 6:48 AM (cron `inbox`, `no_agent` script `inbox_agent.py`).
- **Tier/model:** free local `qwen3:8b` for a one-line categorization; otherwise file enumeration.
- **Deliver:** writes `comms/inbox.md` + `state.json` slice.

## What it does (as implemented)
- Watches `Harmony/00_Inbox/` for new files since last run.
- Lists them with a suggested routing (which tracker/folder they belong to).
- Flags anything older than N days still untouched.

## Output (writes)
- `comms/inbox.md` — the inbox triage source.
- `state.json` slice `inbox`.

## Hard rule
Never moves/deletes files automatically — suggests routing only.

## Done-when
New inbox items listed in the brief; stale items flagged; nothing auto-filed.

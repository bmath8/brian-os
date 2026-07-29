# Agent 09 — Calendar
_Brings Brian's day into the brief from his real calendar._

- **Owns:** the "Today" / schedule section of the brief.
- **Why it exists:** the brief said "here's your day" but had no actual calendar. _Solves:_ morning surprise meetings.
- **Cadence:** daily, 6:55 AM (cron `calendar`, `no_agent` script `calendar_agent.py`).
- **Tier/model:** free local `qwen3:8b` for phrasing; data comes from a **private iCal feed** (wired 2026-06-20, live).
- **Deliver:** writes `comms/calendar.md` + `state.json` slice.

## What it does (as implemented)
- Pulls the day's events from the private iCal feed (Google Calendar → Harmony-linked).
- Summarizes timing, travel/ prep buffers, conflicts.
- Surfaces the next commitment first.

## Output (writes)
- `comms/calendar.md` — the schedule section source.
- `state.json` slice `calendar`.

## Hard rule
Read-only. Never creates/modifies calendar events.

## Done-when
Schedule section present in the brief; matches the real calendar; no fabricated events.

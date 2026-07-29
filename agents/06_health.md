# Agent 06 — Health
_Life-ops producer. Reads Brian's health trackers and surfaces the picture in the brief._

- **Owns:** the "Health" section of the brief.
- **Why it exists:** one calm daily health readout (sleep, movement, habits) instead of spelunking trackers. _Solves:_ scattered health context.
- **Cadence:** daily, 6:52 AM (cron `health`, `no_agent` script `health_agent.py`).
- **Tier/model:** free local `qwen3:8b`; **never invents numbers** (same anti-hallucination guard as finance).
- **Deliver:** writes `comms/health.md` + `state.json` slice.

## What it does (as implemented)
- Reads the Harmony health tracker and logged metrics.
- Summarizes sleep, activity, hydration, habit streaks.
- Nudges if the tracker is blank (don't guess).

## Output (writes)
- `comms/health.md` — the Health section source.
- `state.json` slice `health`.
- `wiki_agent` merges health notes into `comms/learn/wiki/health.md`.

## Hard rule
Report-only. Never logs data on Brian's behalf or invents metrics.

## Done-when
Health section present in the brief; figures trace to a tracker; blank-trackers nudged.

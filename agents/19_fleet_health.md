# Agent 19 — Fleet Health (log_analyzer)
_Turns the write-only run ledger into a health summary._

- **Owns:** `comms/fleet_health.md` — per-agent reliability over a rolling window.
- **Why it exists:** an agent can fail for days and never alert. This surfaces silent degradation. _Solves:_ "everything's green" while something's been red for a week.
- **Cadence:** daily 6:59 AM (cron `fleet-health`, `no_agent` script `log_analyzer.py`).
- **Tier/model:** no model — pure parse of `logs/run_log.md`.
- **Deliver:** writes `comms/fleet_health.md` + `state.json` slice.

## What it does (as implemented)
- Parses `logs/run_log.md` lines (`ISO | agent | tierN | status | detail [| Nms]`).
- Per agent: runs, failures, fail %, last status + time, avg/max latency.
- Flags: any agent with failures, or no *successful* run in >36h.

## Output (writes)
- `comms/fleet_health.md` — the health table + flags.
- `state.json` slice `log_analyzer`.
- Consumed by dashboard + weekly-review.

## Hard rule
Read-only analysis. Never mutates logs or agent state.

## Done-when
Health table reflects the last 7 days; silent failures flagged; no false "all clear."

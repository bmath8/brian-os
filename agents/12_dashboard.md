# Agent 12 — Dashboard (build_dashboard)
_The live HTML ops view over the blackboard._

- **Owns:** `comms/dashboard.html` — a refreshable status page for the whole fleet.
- **Why it exists:** a human-readable, always-current view of fleet health without reading raw `comms/`. _Solves:_ "what's the fleet doing right now?"
- **Cadence:** hourly at :05 (cron `dashboard`, `no_agent` script `build_dashboard.py`).
- **Tier/model:** no model — pure render of `state.json` + `comms/*.md` + `resource_status.json`.
- **Deliver:** writes `comms/dashboard.html` (latest), reads prior for deltas.

## What it does (as implemented)
- Aggregates every agent's `state.json` slice (last run, status, summary, needs_human).
- Renders disk/RAM/VRAM from `resource_status.json`, the watchdog status line, and the apps-vs-target scoreboard.
- Highlights `needs_human[]` items and any Red/Yellow guardrail flag.

## Output (writes)
- `comms/dashboard.html` — open in a browser for the live picture.

## Hard rule
Read-only render. Never mutates agent state.

## Done-when
Dashboard reflects the last hourly tick; flags visible; one file, no external deps.

# Agent 02 — System Watchdog
_Health + self-heal. Keeps the fleet's host (Windows box) alive and reports problems before they page._

- **Owns:** host health, Ollama/gateway liveness, disk/RAM pressure, self-heal of dead processes.
- **Why it exists:** a dead process or full disk silently kills the whole fleet (2026-07-10: a dead `process_guardian` cascaded to 0.4 GB free). _Solves:_ silent degradation, outages.
- **Cadence:** every 4 hours (cron `system-watchdog`, `no_agent` script `system_watchdog.py`).
- **Tier/model:** no model needed — pure deterministic shell/Python checks; `hermes doctor` invocation.
- **Deliver:** writes `comms/system_status.md` + `state.json` slice; alerts via Telegram on threshold breach.

## What it does (as implemented)
- Runs `hermes doctor` and acts on its structured health report.
- Disk check (native `C:\`, not WSL `/mnt/c`), RAM/commit pressure, VRAM free (gates the big model).
- **Heartbeat**: writes `.guardian_beat`; a liveness alert fires if the watchdog itself goes quiet.
- Probes resources via `runtime/resource_probe.ps1` → `comms/resource_status.json` (read by the brief, dashboard, and `fleet_common.model_for()`).
- Revives dead gateway/Ollama via the keepalive chain; logs to `logs/revives.log`.

## Output (writes)
- `comms/system_status.md` (Status line the brief reads).
- `comms/resource_status.json` (RAM/commit/VRAM snapshot).
- `state.json` slice `system`.

## Hard rule
Never auto-remediates user-facing things (passwords, payments, permission dialogs). Reports, revives infra only.

## Done-when
All-clear status line present each tick; any breach alerted within one cycle; `.guardian_beat` fresh.

# WSL-era legacy scripts (archived 2026-06-19)

These ran the fleet when it was hosted in **WSL2**. The fleet migrated to **native
Windows Hermes** on 2026-06-19 (WSL 2.6.1.0 had a VM-teardown bug). They are kept for
reference/rollback only — **not used by the native fleet.**

- `start_gateway_if_down.sh`, `restart_gw.sh` — WSL systemd gateway self-heal (native uses `hermes gateway` + the Startup keepalive).
- `deploy_to_hermes.sh` — WSL deploy (native deploys via PowerShell `Copy-Item` to `%LOCALAPPDATA%\hermes\scripts`).
- `backup_harmony.sh` — superseded by `runtime/backup_harmony.py` (cross-platform, robocopy on Windows).
- `fleet_status.sh` — superseded by `runtime/build_dashboard.py` + the `/fleet` Telegram command.
- `safe_model.py` — superseded by `fleet_common.model_for()`.
- `install_watchdog_task.ps1` — superseded by the Startup keepalive (`BrianOS-Keepalive.vbs`).
- `wslconfig.reference`, `start_fleet.cmd` — WSL `.wslconfig` + WSL logon launcher.

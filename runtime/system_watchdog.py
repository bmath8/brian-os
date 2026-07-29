#!/usr/bin/env python3
"""System Watchdog agent - first producer on the comms blackboard.
Checks disk, Ollama, gateway, and backup freshness; writes comms/system_status.md
and updates state.json with any needs_human[] alerts. Self-heals Ollama + the
gateway. Runs on a schedule; the Chief of Staff brief reads its output."""
import os, sys, json, urllib.request, subprocess, datetime, glob, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

BK = fc.HARMONY_BACKUP
PS = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
ENSURE_OLLAMA = r"C:\Brian\02_Projects\brian-os-fleet\runtime\ensure_ollama.ps1"
RESOURCE_PROBE = r"C:\Brian\02_Projects\brian-os-fleet\runtime\resource_probe.ps1"


def _telegram_token():
    """Read TELEGRAM_BOT_TOKEN from env or the Hermes .env (no extra deps)."""
    tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    if tok:
        return tok.strip()
    for envpath in (os.path.join(os.environ.get("HERMES_HOME", ""), ".env"),
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", ".env")):
        if envpath and os.path.isfile(envpath):
            for line in fc.read(envpath).splitlines():
                if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def main():
    alerts, lines = [], []

    # Disk
    try:
        _, _, free = shutil.disk_usage("C:\\" if fc.WINDOWS else "/mnt/c")
        g = free / 1e9
        lines.append(f"Disk C: {g:.0f} GB free")
        if g < 15:
            alerts.append(f"Low disk: only {g:.0f} GB free on C:")
    except Exception as e:
        lines.append(f"Disk: check failed ({e})")

    # Ollama
    try:
        urllib.request.urlopen(f"{fc.ollama_url()}/api/tags", timeout=5)
        lines.append("Ollama: reachable")
    except Exception:
        try:
            subprocess.run(PS + [ENSURE_OLLAMA], timeout=45, capture_output=True)
            lines.append("Ollama: was down - auto-restart attempted")
            alerts.append("Ollama was down - auto-restarted (verify next run)")
        except Exception:
            lines.append("Ollama: DOWN")
            alerts.append("Ollama not reachable and restart failed")

    # Gateway - OS-aware. Native Windows: `hermes gateway status/start` (Scheduled Task
    # + detached pythonw). WSL: the race-safe, systemd-aware bash self-heal (G16/G18).
    if fc.WINDOWS:
        hexe = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes",
                            "hermes-agent", "venv", "Scripts", "hermes.exe")
        try:
            r = subprocess.run([hexe, "gateway", "status"], timeout=30, capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            # NOTE: "Gateway is NOT running" also contains "running" - the exact string-match
            # bug that silently disabled the keepalive before 06-20. Exclude the negative.
            _gw_out = ((r.stdout or "") + (r.stderr or "")).lower()
            if "running" in _gw_out and "not running" not in _gw_out:
                lines.append("Gateway: running")
            else:
                # Relaunch via the hidden-console VBS, NOT `hermes gateway start`:
                # hermes' own start detaches with pythonw (no console), which makes
                # every console child (node sidecar, cron) pop a visible window.
                vbs = r"C:\Brian\02_Projects\brian-os-fleet\runtime\start_gateway_hidden.vbs"
                subprocess.Popen(["wscript.exe", vbs])
                lines.append("Gateway: was down - relaunched via hidden-console VBS")
                alerts.append("Hermes gateway was down - auto-started (verify)")
        except Exception as e:
            lines.append(f"Gateway: check failed ({e})")
    else:
        try:
            r = subprocess.run(["bash", os.path.expanduser("~/.hermes/start_gateway_if_down.sh")],
                               timeout=60, capture_output=True, text=True)
            mark = (r.stdout or "").strip().splitlines()[-1] if (r.stdout or "").strip() else ""
            if mark == "GW:up":
                lines.append("Gateway: running")
            elif mark == "GW:healed":
                lines.append("Gateway: was down - auto-restarted OK")
                alerts.append("Hermes gateway was down - auto-restarted (verify briefs)")
            else:
                lines.append("Gateway: DOWN")
                alerts.append("Hermes gateway down and auto-restart failed")
        except Exception as e:
            lines.append(f"Gateway: check failed ({e})")

    # Telegram reachability - NON-DISRUPTIVE liveness probe (getMe). Confirms the bot
    # token is valid and Telegram's API is reachable (catches token revocation / network
    # / Telegram outage). Deliberately NOT getUpdates: that long-poll conflicts with the
    # gateway's own poller (409) and can knock IT offline. getMe never conflicts.
    # Caveat: this does NOT detect a "process up but poll task wedged" gateway - that
    # needs a gateway heartbeat (vendor change). The external dead-man's-switch covers
    # the catastrophic case. Degrades silently if no token configured.
    try:
        token = _telegram_token()
        if token:
            req = urllib.request.Request(f"https://api.telegram.org/bot{token}/getMe",
                                         headers={"User-Agent": "BrianOS watchdog"})
            d = json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
            if d.get("ok"):
                lines.append(f"Telegram API: reachable (@{d['result'].get('username','?')})")
            else:
                lines.append("Telegram API: getMe not ok")
                alerts.append(f"Telegram getMe failed: {d.get('description','')[:80]}")
    except Exception as e:
        lines.append("Telegram API: unreachable")
        alerts.append(f"Telegram API unreachable ({type(e).__name__}) - token/network/outage")

    # Morning brief actually DELIVERED today? (#2) A no_agent job can run + log "ok"
    # yet silently skip delivery ([SILENT]/encoding/timeout) - the exact failure that
    # hid the 06-20 outage. After the brief hour, verify it ran today with no delivery
    # error; otherwise alert. Reads the cron ledger (source of truth for delivery).
    try:
        jpath = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "cron", "jobs.json")
        if os.path.isfile(jpath):
            jobs = json.load(open(jpath, encoding="utf-8")).get("jobs", [])
            brief = next((j for j in jobs if j.get("name") == "daily-brief"), None)
            if brief and brief.get("enabled", True):
                today = datetime.date.today().isoformat()
                lr = (brief.get("last_run_at") or "")[:10]
                derr = (brief.get("last_delivery_error") or "").strip()
                if datetime.datetime.now().hour >= 8:          # judge only after the brief window
                    if lr != today:
                        alerts.append(f"Morning brief did NOT run today (last run: {lr or 'never'})")
                    elif derr:
                        alerts.append(f"Morning brief failed to deliver: {derr[:80]}")
                    else:
                        lines.append("Brief: delivered today")
                else:
                    lines.append("Brief: pre-window")
    except Exception as e:
        lines.append(f"Brief check: failed ({e})")

    # Hermes doctor (native diagnostics; the report's recommended health check).
    # Only flag real FAILURES (X), not warnings like "Nous Portal not logged in".
    if fc.WINDOWS:
        try:
            hexe = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes",
                                "hermes-agent", "venv", "Scripts", "hermes.exe")
            r = subprocess.run([hexe, "doctor"], timeout=60, capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            out = (r.stdout or "") + (r.stderr or "")
            bad = [ln.strip() for ln in out.splitlines()
                   if ("✗" in ln or "✘" in ln or "FAIL" in ln.upper())]
            if bad:
                lines.append(f"Hermes doctor: {len(bad)} issue(s)")
                alerts.append("hermes doctor flagged: " + "; ".join(b[:80] for b in bad[:2]))
            else:
                lines.append("Hermes doctor: healthy")
        except Exception as e:
            lines.append(f"Hermes doctor: check failed ({e})")

    # Harmony backup freshness. Judge by the mirror's OWN .last_backup stamp (when the
    # job last ran), NOT by newest file mtime -- robocopy preserves source timestamps,
    # so quiet Harmony weeks made a healthy nightly mirror look "stale" (false alert).
    try:
        stamp = os.path.join(BK, ".last_backup")
        if os.path.isfile(stamp):
            age = (datetime.datetime.now().timestamp() - os.path.getmtime(stamp)) / 86400
            lines.append(f"Harmony backup: mirror ran {age:.1f} days ago")
            if age > 2:
                alerts.append(f"Harmony backup job hasn't run in {age:.0f} days - check the 1:30 cron")
        else:
            files = [p for p in glob.glob(BK + "/**/*", recursive=True) if os.path.isfile(p)]
            if files:
                newest = max(os.path.getmtime(p) for p in files)
                age = (datetime.datetime.now().timestamp() - newest) / 86400
                lines.append(f"Harmony backup: {age:.1f} days old ({len(files)} files, no stamp yet)")
            else:
                alerts.append("Harmony backup missing")
    except Exception as e:
        lines.append(f"Backup: check failed ({e})")

    # Host resources via the PowerShell probe (WSL's /proc only sees the VM)
    try:
        subprocess.run(PS + [RESOURCE_PROBE], timeout=30, capture_output=True)
        r = json.load(open(f"{fc.COMMS}/resource_status.json"))
        lines.append(f"RAM: {r['ram_free_gb']} GB free ({r['ram_pct']}% used) | "
                     f"commit {r['commit_pct']}% | VRAM {r['vram_used_mb']}/{r['vram_total_mb']} MB")
        if r['commit_pct'] >= 95:
            alerts.append(f"SEVERE memory pressure (commit {r['commit_pct']}%) - agents should run 8B only; "
                          f"pagefile thrashing. #1 fix: 64GB DDR5 RAM")
        elif r['commit_pct'] >= 88 or r['ram_pct'] >= 90:
            alerts.append(f"High memory pressure (RAM {r['ram_pct']}%, commit {r['commit_pct']}%) - "
                          f"prefer 8B models, close heavy apps")
    except Exception as e:
        lines.append(f"Resources: probe failed ({e})")

    # Guardian liveness (2026-07-11): the guardian watches everything else; nothing
    # watched the guardian - it aborted silently for days ($pid bug) while orphans
    # ate the RAM and the pagefile ate the disk. Its log is touched every ~3 min tick,
    # so >30 min of silence means the guardian OR the keepalive loop is dead.
    try:
        # Prefer the dedicated heartbeat file - guardian.log can be blocked by a
        # reader's file handle (seen live: Claude Desktop) without the guardian
        # being dead. Fall back to the log for pre-heartbeat installs.
        glog = os.path.join(fc.LOGS, ".guardian_beat")
        if not os.path.isfile(glog):
            glog = os.path.join(fc.LOGS, "guardian.log")
        if os.path.isfile(glog):
            gage = (datetime.datetime.now().timestamp() - os.path.getmtime(glog)) / 60
            if gage > 30:
                alerts.append(f"Process guardian silent {gage:.0f} min - keepalive loop may be down")
            else:
                lines.append(f"Guardian: alive ({gage:.0f} min ago)")
        else:
            alerts.append("Process guardian has never logged - check the keepalive")
    except Exception as e:
        lines.append(f"Guardian check: failed ({e})")

    now = fc.now()
    status = "ALL CLEAR" if not alerts else f"{len(alerts)} alert(s)"
    md = f"# System Status - {now}\n\nStatus: {status}\n\n## Checks\n" + "\n".join(f"- {l}" for l in lines) + "\n"
    if alerts:
        md += "\n## Alerts\n" + "\n".join(f"- {a}" for a in alerts) + "\n"
    fc.atomic_write(f"{fc.COMMS}/system_status.md", md)

    fc.state_update("watchdog", {"last_run": now, "status": "ok" if not alerts else "alert",
                                 "summary": status, "needs_human": alerts})

    # Alert ONLY when the alert set changes (chronic conditions don't re-ping every 4h).
    lastf = f"{fc.COMMS}/.last_alerts"
    if alerts:
        # Normalize numbers out of the signature: "RAM 88%" vs "RAM 89%" is the SAME
        # chronic condition -- embedding live numbers made the change-detector re-ping
        # Telegram every 4h anyway (alert fatigue defeats the alert).
        import re as _re
        sig = _re.sub(r"\d+(?:\.\d+)?", "#", "|".join(sorted(alerts)))
        prev = fc.read(lastf)
        if sig != prev:
            fc.atomic_write(lastf, sig)
            _alert_msg = f"\U0001f6a8 System Watchdog - {now}\n" + "\n".join(f"- {a}" for a in alerts)
            fc.telegram_send(_alert_msg, urgent=True)      # direct API (update-proof)
            print(fc.ascii_fold(_alert_msg))
    else:
        try:
            os.remove(lastf)
        except Exception:
            pass

    fc.log_run("watchdog", "ok" if not alerts else "alert", f"{len(alerts)} alert(s)")
    # Heartbeat to the external dead-man's-switch every 4h (no-op until configured).
    fc.ping_healthcheck()


if __name__ == "__main__":
    main()

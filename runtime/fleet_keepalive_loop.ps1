# Persistent keepalive loop — launched hidden at logon (no admin / scheduled task needed).
# Calls fleet_keepalive.ps1 every 3 minutes so a dead WSL/gateway/Ollama is revived
# within minutes, for the whole time you're logged in. Never exits on error.
$env:PYTHONUTF8 = '1'
$keep = 'C:\Brian\02_Projects\brian-os-fleet\runtime\fleet_keepalive.ps1'
$py   = Join-Path $env:LOCALAPPDATA 'hermes\hermes-agent\venv\Scripts\python.exe'
$boot = 'C:\Brian\02_Projects\brian-os-fleet\runtime\boot_smoke.py'

# First tick brings Ollama + the gateway up; then send one boot confirmation (#6).
try { & $keep } catch { }
Start-Sleep -Seconds 18
try { & $py $boot 'Fleet booted (login)' 2>&1 | Out-Null } catch { }

# Catch-up brief: Brian shuts the PC down to manage heat/electricity, so the machine
# is often OFF at 7am and the morning brief is skipped. On the first boot of the day
# (after the brief hour), deliver today's brief now instead of losing it. Once/day.
try {
    $hh = Join-Path $env:LOCALAPPDATA 'hermes\hermes-agent\venv\Scripts\hermes.exe'
    $brief = ((Get-Content "$env:LOCALAPPDATA\hermes\cron\jobs.json" -Raw | ConvertFrom-Json).jobs |
              Where-Object { $_.name -eq 'daily-brief' })
    $today = (Get-Date).ToString('yyyy-MM-dd')
    $lr = if ($brief.last_run_at) { ([datetime]$brief.last_run_at).ToString('yyyy-MM-dd') } else { '' }
    $stamp = Join-Path $env:LOCALAPPDATA "hermes\.brief_catchup_$today"
    if ((Get-Date).Hour -ge 7 -and $lr -ne $today -and -not (Test-Path $stamp)) {
        & $hh cron run daily-brief 2>&1 | Out-Null
        New-Item -ItemType File -Path $stamp -Force | Out-Null
    }
} catch { }

while ($true) {
    Start-Sleep -Seconds 180
    try { & $keep } catch { }
}

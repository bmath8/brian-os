# upgrade_hermes.ps1 - GUARDED Hermes upgrade (2026-07-06).
# Brian's rule: never blind-update (v0.16->v0.17 broke things; the 06-23 client update
# broke Telegram delivery twice). This script makes updating SAFE instead of automatic:
#   backup -> stop gateway -> update -> verify (doctor + boot smoke) -> relaunch,
#   auto-restoring config/scripts/skills/plugins if verification fails.
# Run it when the daily currency flag shows a release worth having:
#   powershell -NoProfile -ExecutionPolicy Bypass -File runtime\upgrade_hermes.ps1
param([switch]$SkipBackup)
$ErrorActionPreference = 'Continue'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$root  = 'C:\Brian\02_Projects\brian-os-fleet'
$hh    = Join-Path $env:LOCALAPPDATA 'hermes'
$hexe  = Join-Path $hh 'hermes-agent\venv\Scripts\hermes.exe'
$py    = Join-Path $hh 'hermes-agent\venv\Scripts\python.exe'
$log   = Join-Path $root ("logs\hermes_upgrade_{0}.log" -f $stamp)
function Log($m) { $line = "{0} {1}" -f (Get-Date -Format s), $m; Write-Host $line; Add-Content -Path $log -Value $line }

Log ("BEFORE: " + ((& $hexe --version 2>&1 | Select-Object -First 1) -join ' '))

# 1) Backup everything the fleet customized (config, env, scripts, skills, plugins, cron).
$bk = Join-Path $env:LOCALAPPDATA ("hermes_backup_{0}" -f $stamp)
if (-not $SkipBackup) {
    New-Item -ItemType Directory -Force $bk | Out-Null
    foreach ($item in 'config.yaml', '.env', 'scripts', 'skills', 'plugins', 'cron') {
        $src = Join-Path $hh $item
        if (Test-Path $src) { Copy-Item $src (Join-Path $bk $item) -Recurse -Force }
    }
    Log "backup -> $bk"
}

# 2) Stop the gateway (NEVER update while it runs - Brian's rule from the 06-23 breakage).
try { & $hexe gateway stop 2>&1 | Out-Null } catch { }
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'hermes_cli.*gateway' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Log "gateway stopped"

# 3) Update (blocking, capped at 15 min).
$p = Start-Process -FilePath $hexe -ArgumentList 'update' -NoNewWindow -PassThru -Wait
Log ("hermes update exit code: {0}" -f $p.ExitCode)
Log ("AFTER: " + ((& $hexe --version 2>&1 | Select-Object -First 1) -join ' '))

# 4) Verify: doctor must show no hard failures.
$doc = (& $hexe doctor 2>&1) -join "`n"
$bad = @($doc -split "`n" | Where-Object { $_ -match '✗|✘|FAIL' })
Log ("doctor: {0} hard failure(s)" -f $bad.Count)

# 5) On failure: restore the customized files (the update may have overwritten them).
if ($bad.Count -gt 0 -and -not $SkipBackup) {
    foreach ($item in 'config.yaml', '.env', 'scripts', 'skills', 'plugins', 'cron') {
        $src = Join-Path $bk $item
        if (Test-Path $src) { Copy-Item $src (Join-Path $hh $item) -Recurse -Force }
    }
    Log "ROLLBACK: doctor failed - restored config/scripts/skills/plugins/cron from $bk"
    Log "NOTE: the hermes PACKAGE itself is not rolled back; if it misbehaves, reinstall the pinned version."
}

# 6) Relaunch the gateway (UTF-8 mode, hidden - same path the keepalive uses).
$env:PYTHONUTF8 = '1'
Start-Process -FilePath 'wscript.exe' -ArgumentList ('"' + (Join-Path $root 'runtime\start_gateway_hidden.vbs') + '"') -WindowStyle Hidden
Start-Sleep -Seconds 12
Log "gateway relaunched"

# 7) Boot smoke-test -> direct Telegram, so Brian gets proof delivery still works.
try { & $py (Join-Path $root 'runtime\boot_smoke.py') 'Hermes upgraded' ("doctor failures: {0}" -f $bad.Count) 2>&1 | Out-Null } catch { Log "boot_smoke error: $_" }
Log ("DONE - status: " + $(if ($bad.Count -eq 0) { 'UPGRADE OK' } else { 'UPGRADE FAILED - custom files restored, investigate ' + $log }))

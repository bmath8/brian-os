# process_guardian.ps1 - keep ONLY the right things running on Brian's RAM-tight (16GB) box.
#
# The problem it solves: Claude Desktop's MCP connectors (windows-mcp, pdf, prisma, ...) respawn
# on every reconnect and DON'T close the old process -> duplicate/orphan background procs pile up
# and eat RAM. Same for the occasional stuck fleet cron job. This reaps those SAFELY and reports.
#
# SAFE BY DESIGN - it never touches:
#   - the apps Brian actually uses (Claude main window, Chrome, Edge) or anything with a visible window
#   - the live fleet singletons (the ONE gateway, the keepalive, Ollama + its model servers, the iMessage sidecar)
#   - system processes
# It only reaps: duplicate MCP connector processes (keeps the NEWEST = live one, kills older orphans
# >5 min old) and stuck fleet cron python (>15 min). Every action is guarded; it can't crash the keepalive.
#
# Usage:  powershell -File process_guardian.ps1            # reap + print report
#         powershell -File process_guardian.ps1 -Quiet     # reap silently (for the keepalive)
param([switch]$Quiet)
$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\Brian\02_Projects\brian-os-fleet'
$log  = Join-Path $root 'logs\guardian.log'
function Log($m){ try { Add-Content $log ("{0} {1}" -f (Get-Date -Format s), $m) } catch {} }
try { if ((Test-Path $log) -and (Get-Item $log).Length -gt 500KB) { (Get-Content $log -Tail 300) | Set-Content $log } } catch {}
$now = Get-Date
$killed = @()
# NOTE: parameter must NOT be named $pid - that's a read-only PowerShell automatic
# variable; binding it throws a terminating error that aborted this whole script
# (silent since ship: no reaping, no keepalive-ensure, no RAM report). Fixed 2026-07-11.
function AgeMin($procId){ try { [math]::Round(($now - (Get-Process -Id $procId -EA SilentlyContinue).StartTime).TotalMinutes) } catch { 999 } }
function Born($cim){ try { [Management.ManagementDateTimeConverter]::ToDateTime($cim.CreationDate) } catch { Get-Date 0 } }

# --- 1) Duplicate MCP connector processes (keep newest, reap older orphans > 5 min) ---
# node-based MCP servers (pdf/prisma/@modelcontextprotocol). NEVER the iMessage sidecar.
$nodeMcp = Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
  Where-Object { $_.CommandLine -match 'server-pdf|prisma|@modelcontextprotocol|[\\/]mcp[\\/]' -and $_.CommandLine -notmatch 'photon\\sidecar|desktop.?commander' }
$nodeMcp | Group-Object {
    $c = "$($_.CommandLine)"
    if ($c -match 'server-pdf') { 'pdf' } elseif ($c -match 'prisma') { 'prisma' } else { ($c -split '\s+' | Select-Object -Last 1) }
  } | Where-Object { $_.Count -gt 1 } | ForEach-Object {
    ($_.Group | Sort-Object { Born $_ } -Descending | Select-Object -Skip 1) | ForEach-Object {
      if ((AgeMin $_.ProcessId) -ge 5) { & taskkill /PID $_.ProcessId /T /F 2>$null | Out-Null; $killed += "dup node MCP ($($_.ProcessId))"; Log "reaped dup node MCP PID $($_.ProcessId)" }
    }
  }
# windows-mcp.exe duplicate trees (each spawns python children -> /T kills the tree)
$winmcp = @(Get-CimInstance Win32_Process -Filter "Name='windows-mcp.exe'")
if ($winmcp.Count -gt 1) {
  ($winmcp | Sort-Object { Born $_ } -Descending | Select-Object -Skip 1) | ForEach-Object {
    if ((AgeMin $_.ProcessId) -ge 5) { & taskkill /PID $_.ProcessId /T /F 2>$null | Out-Null; $killed += "dup windows-mcp tree ($($_.ProcessId))"; Log "reaped dup windows-mcp tree PID $($_.ProcessId)" }
  }
}

# --- 2) Stuck / orphaned fleet cron python (> 15 min running a fleet script) ---
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" |
  Where-Object { "$($_.CommandLine)" -match 'brian-os-fleet|hermes\\scripts\\' -and "$($_.CommandLine)" -notmatch 'gateway' } |
  ForEach-Object { if ((AgeMin $_.ProcessId) -ge 15) { Stop-Process -Id $_.ProcessId -Force; $killed += "stuck cron ($($_.ProcessId))"; Log "reaped stuck cron PID $($_.ProcessId)" } }

# --- 3) Keepalive: ensure EXACTLY ONE (it's the gateway's watchdog; 0 = unprotected, >1 = waste) ---
# Safe here because the guardian runs via -File, so its own command line is just the script path
# and never matches 'fleet_keepalive_loop' (the inline self-kill trap).
$kas = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { "$($_.CommandLine)" -match 'fleet_keepalive_loop\.ps1' })
if ($kas.Count -eq 0) {
  & wscript.exe "$root\runtime\BrianOS-Keepalive.vbs"; $killed += "relaunched keepalive (was down)"; Log "keepalive was DOWN - relaunched"
} elseif ($kas.Count -gt 1) {
  # Never kill keepalives from here (this guardian is often launched BY the keepalive - killing its
  # own launcher would be the bug we just fixed). Just flag it; dedupe happens at next logon.
  Log "WARN: $($kas.Count) keepalive loops (expected 1)"
}

# --- 4) Heartbeat (2026-07-11) ---
# Liveness stamp in a DEDICATED file no other tool reads. Discovered live: Claude
# Desktop held a read handle on guardian.log, which blocked Add-Content for a DAY
# (silent - Log() swallows errors) and would false-trip the watchdog's liveness
# alert. The beat file is written with Set-Content (rewrite) and read by mtime only.
try { Set-Content (Join-Path $root 'logs\.guardian_beat') (Get-Date -Format s) -EA SilentlyContinue } catch {}

# --- 5) Report ---
$os = Get-CimInstance Win32_OperatingSystem
$freeGB = [math]::Round($os.FreePhysicalMemory/1MB,1); $totGB = [math]::Round($os.TotalVisibleMemorySize/1MB,1)
$pct = [math]::Round(100*($totGB-$freeGB)/$totGB)
# Gateway count = distinct process TREES, not raw process count. Hermes boots the
# gateway as venv\python.exe -m hermes_cli.main gateway run, which then re-execs
# into the pinned .hermes-runtime python -- so ONE healthy gateway is always two
# matching processes in a parent->child pair. Counting raw matches reported
# "gateway=2" forever (2026-07-28 audit), which made the metric useless: a real
# duplicate was indistinguishable from normal. Count only roots: a gateway proc
# whose parent is not itself a gateway.
$gwProcs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" | Where-Object { "$($_.CommandLine)" -match 'hermes_cli.*gateway' })
$gwPids  = $gwProcs | ForEach-Object { $_.ProcessId }
$gw = @($gwProcs | Where-Object { $gwPids -notcontains $_.ParentProcessId }).Count
$ka = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { "$($_.CommandLine)" -match '\-File.*fleet_keepalive_loop' }).Count
$sc = @(Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { "$($_.CommandLine)" -match 'photon\\sidecar' }).Count
Log ("RAM ${freeGB}GB free (${pct}% used) | gateway=$gw keepalive=$ka sidecar=$sc | reaped $($killed.Count)")
if (-not $Quiet) {
  Write-Host ("RAM: {0} GB free / {1} GB ({2}% used)" -f $freeGB,$totGB,$pct)
  Write-Host ("Fleet health: gateway={0} keepalive={1} iMessage-sidecar={2}  (expected 1 / 1 / 1)" -f $gw,$ka,$sc)
  if ($killed.Count) { Write-Host "Reaped $($killed.Count) duplicate/orphan process(es):"; $killed | ForEach-Object { Write-Host "  - $_" } }
  else { Write-Host "No duplicates/orphans to reap right now." }
}

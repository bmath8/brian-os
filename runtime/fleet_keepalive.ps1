# BrianOS Fleet keepalive - NATIVE Windows watchdog (every ~3 min via the Startup loop).
# Keeps Ollama (localhost) + the native Hermes gateway alive, reviving either within
# minutes of a crash/sleep/logon.
#
# 2026-06-20 REWRITE: the old check used  ("$st" -match 'running')  to decide if the
# gateway was up -- but "Gateway is NOT running" ALSO contains "running", so the test was
# ALWAYS true and the gateway was NEVER revived (silent self-heal failure -> total outage).
# We now detect the gateway by its actual PROCESS, which is unambiguous and immune to
# stale PID files. A single-instance guard prevents launching a 2nd gateway (Telegram 409).

$root = 'C:\Brian\02_Projects\brian-os-fleet'
$log  = Join-Path $root 'logs\keepalive.log'
$pw   = Join-Path $env:LOCALAPPDATA 'hermes\hermes-agent\venv\Scripts\pythonw.exe'
$py   = Join-Path $env:LOCALAPPDATA 'hermes\hermes-agent\venv\Scripts\python.exe'

# CRITICAL: run the gateway in Python UTF-8 mode. Hermes runs cron scripts via
# subprocess.run(text=True), which decodes their stdout with the parent's locale
# (cp1252 on Windows). Any emoji in a brief/watchdog message (☀️ 🚨 📚) then throws
# UnicodeDecodeError in the gateway's reader thread -> captured stdout is EMPTY ->
# Hermes logs "[SILENT]" and skips delivery. UTF-8 mode makes the gateway decode
# child output as UTF-8, so emoji-bearing messages actually get delivered.
$env:PYTHONUTF8 = '1'

function Log($m) { try { Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format s), $m) } catch { } }
try { if ((Test-Path $log) -and (Get-Item $log).Length -gt 1MB) { (Get-Content $log -Tail 400) | Set-Content $log } } catch { }

Log "tick"

# 1) Ollama up + bound (native Hermes reaches it on localhost:11434).
try { & (Join-Path $root 'runtime\ensure_ollama.ps1') 2>&1 | Out-Null } catch { Log "ensure_ollama error: $_" }

# 2) Gateway up? Count REAL pythonw processes whose command line runs the gateway.
#    (2 = launcher+worker is normal; >=1 means it's up.) No string-match guessing.
function Get-GatewayProcs {
    # Match BOTH pythonw.exe (keepalive's own launch) AND python.exe - a `hermes
    # gateway start`/update relaunch uses the SYSTEM python.exe, which a pythonw-only
    # filter misses, making the keepalive think the gateway is down and crash-loop
    # launching duplicates that the single-instance lock then refuses. (Fixed 2026-06-23.)
    @(Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -match 'hermes_cli.*gateway' })
}
try {
    $procs = Get-GatewayProcs
    if ($procs.Count -ge 1) {
        Log ("ok - gateway running ({0} proc)" -f $procs.Count)
    } else {
        # Single-instance guard: re-check immediately before launching to avoid a 409 race.
        Start-Sleep -Milliseconds 500
        if ((Get-GatewayProcs).Count -eq 0) {
            Start-Process -FilePath 'wscript.exe' -ArgumentList ('"' + (Join-Path $root 'runtime\start_gateway_hidden.vbs') + '"') -WindowStyle Hidden
            Log "REVIVED - gateway was DOWN, launched via hidden-console VBS (no child window popups)"
            # Record the revive + detect a crash loop (#5): >=3 revives in 60 min.
            $rl = Join-Path $root 'logs\revives.log'
            try { Add-Content -Path $rl -Value (Get-Date -Format s) } catch { }
            $recent = 0
            try {
                $cut = (Get-Date).AddMinutes(-60)
                $recent = @(Get-Content $rl -ErrorAction SilentlyContinue | Where-Object { try { [datetime]::Parse($_) -ge $cut } catch { $false } }).Count
                if ((Get-Item $rl).Length -gt 50KB) { (Get-Content $rl -Tail 50) | Set-Content $rl }
            } catch { }
            $warn = ''
            if ($recent -ge 3) { $warn = "CRASH LOOP: gateway revived $recent times in the last hour - likely VRAM/RAM pressure (close Claude Desktop/Codex/Chrome tabs)."; Log "CRASH-LOOP ($recent revives/hr)" }
            # Boot/recovery smoke-test -> direct Telegram (#6). Give the gateway a moment to bind.
            Start-Sleep -Seconds 10
            try { & $py (Join-Path $root 'runtime\boot_smoke.py') 'Gateway revived' $warn 2>&1 | Out-Null } catch { Log "boot_smoke error: $_" }
        }
    }
} catch { Log "gateway check error: $_" }

# 2b) WEDGE DETECTION (2026-07-06): catches "process up but cron/poll dead" - the one
#     failure neither the process count above nor the watchdog's getMe can see.
#     The dashboard cron is hourly, so: if the gateway has been up >90 min AND no cron
#     job has run in >90 min, the scheduler/poller is wedged -> kill the gateway; the
#     next tick's revive path relaunches it clean. Uptime guard avoids boot false-kills.
try {
    $jobsPath = Join-Path $env:LOCALAPPDATA 'hermes\cron\jobs.json'
    $wprocs = Get-GatewayProcs
    if ((Test-Path $jobsPath) -and $wprocs.Count -ge 1) {
        $oldestStart = ($wprocs | ForEach-Object { $_.CreationDate } | Sort-Object | Select-Object -First 1)
        $upMin = ((Get-Date) - $oldestStart).TotalMinutes
        if ($upMin -gt 90) {
            $jobs = (Get-Content $jobsPath -Raw | ConvertFrom-Json).jobs | Where-Object { $_.enabled -ne $false }
            $lastRuns = @($jobs | ForEach-Object { $_.last_run_at } | Where-Object { $_ } |
                ForEach-Object { try { [datetime]::Parse($_) } catch { } } | Where-Object { $_ })
            if ($lastRuns.Count -gt 0) {
                $newest = ($lastRuns | Sort-Object | Select-Object -Last 1)
                $staleMin = ((Get-Date) - $newest).TotalMinutes
                if ($staleMin -gt 90) {
                    $wprocs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
                    Log ("WEDGE-KILL - gateway up {0:n0} min but newest cron run is {1:n0} min old; killed for clean revive next tick" -f $upMin, $staleMin)
                }
            }
        }
    }
} catch { Log "wedge check error: $_" }

# 3) Keep the model warm during the morning brief window (06:30-07:20) so the 7:00 brief
#    runs in ~20s instead of a cold ~2-3 min load that overruns the cron and gets dropped.
#    Outside that window we let it unload to spare RAM (16GB box).
try {
    $now = Get-Date
    $mins = $now.Hour * 60 + $now.Minute
    # Sunday 16:10-17:10 added 2026-07-11: weekly-review (17:00) + currency-weekly (16:30)
    # + wiki (16:45) all hit a cold model on the quietest day of the week.
    $sundayWindow = ($now.DayOfWeek -eq 'Sunday' -and $mins -ge 970 -and $mins -le 1030)
    if (($mins -ge 390 -and $mins -le 440) -or $sundayWindow) {
        $body = '{"model":"qwen3:8b","prompt":"ok","stream":false,"keep_alive":"30m","options":{"num_predict":1}}'
        Invoke-RestMethod -Uri 'http://localhost:11434/api/generate' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 120 | Out-Null
        Log "prewarm - model kept warm for the morning brief"
    }
} catch { Log "prewarm error: $_" }

# 4) Process hygiene (every tick, ~3 min): reap duplicate/orphan background procs - the Claude MCP
#    connectors that respawn and don't close, plus stuck cron - and keep the fleet singletons right.
#    Runs inside this hidden keepalive, so it never flashes a window; guarded so it can't break the loop.
try { & 'C:\Brian\02_Projects\brian-os-fleet\runtime\process_guardian.ps1' -Quiet } catch { Log "guardian error: $_" }

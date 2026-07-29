# deploy_fleet.ps1 - safe deploy of the fleet's Python scripts to the live Hermes
# scripts dir, with a timestamped backup, a self-written CHANGELOG (#64), and a
# one-command rollback (#63). Makes shipping fearless: every deploy is reversible.
#
#   Deploy:    powershell -File deploy_fleet.ps1 -Message "Batch C - hardening"
#   Rollback:  powershell -File deploy_fleet.ps1 -Rollback
#   List:      powershell -File deploy_fleet.ps1 -List
param([switch]$Rollback, [switch]$List, [string]$Message = "")
$ErrorActionPreference = 'Stop'
$repo      = 'C:\Brian\02_Projects\brian-os-fleet'
$src       = Join-Path $repo 'runtime'
$dst       = Join-Path $env:LOCALAPPDATA 'hermes\scripts'
$bkroot    = Join-Path $env:LOCALAPPDATA 'hermes\scripts_backups'
$changelog = Join-Path $repo 'CHANGELOG.md'
New-Item -ItemType Directory -Force -Path $bkroot, $dst | Out-Null
function Log($m) { if (-not (Test-Path $changelog)) { Set-Content $changelog "# Fleet CHANGELOG`n_Auto-written by deploy_fleet.ps1._`n" }; Add-Content $changelog $m }

if ($List) {
    Get-ChildItem $bkroot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending |
        Select-Object -First 15 | ForEach-Object { "  $($_.Name)  ($((Get-ChildItem "$($_.FullName)\*.py" -ErrorAction SilentlyContinue).Count) scripts)" }
    return
}

if ($Rollback) {
    $last = Get-ChildItem $bkroot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $last) { Write-Host "No backup found to roll back to."; exit 1 }
    Copy-Item "$($last.FullName)\*.py" -Destination $dst -Force
    Log ("- {0} ROLLBACK -> restored backup {1}" -f (Get-Date -Format s), $last.Name)
    Write-Host "Rolled back to backup $($last.Name). Restart the gateway to pick up cron-script changes."
    return
}

# 1) Back up the current LIVE scripts before overwriting.
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$bk = Join-Path $bkroot $stamp
New-Item -ItemType Directory -Force -Path $bk | Out-Null
if (Test-Path "$dst\*.py") { Copy-Item "$dst\*.py" -Destination $bk -Force }

# 2) Deploy all repo runtime scripts.
Copy-Item "$src\*.py" -Destination $dst -Force
$n = (Get-ChildItem "$src\*.py").Count

# 3) Self-written changelog entry (#64), tagged with the git sha.
$sha = (git -C $repo rev-parse --short HEAD 2>$null)
Log ("- {0} deploy {1} scripts @ {2} - {3}  [backup: {4}]" -f (Get-Date -Format s), $n, $sha, ($Message -replace '\r?\n',' '), $stamp)

# 4) Prune old backups (keep last 12).
Get-ChildItem $bkroot -Directory | Sort-Object Name -Descending | Select-Object -Skip 12 |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host "Deployed $n scripts (backup $stamp). Rollback: deploy_fleet.ps1 -Rollback"

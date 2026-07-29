# stage_fleet.ps1 - validate the fleet on a COPY before touching live (#65).
#
# Copies runtime + tests to a staging dir and runs the full 52-test suite THERE,
# so a risky change (model swap, Hermes update, refactor) is proven off-live first.
# The tests use temp dirs (FLEET_ROOT/COMMS overrides), so this never touches the
# live blackboard. Use before any deploy you're unsure about:
#
#   powershell -File stage_fleet.ps1        # stage + test the current repo
#
# Exit 0 = safe to deploy; non-zero = do NOT deploy.
param([string]$Stage = "C:\Brian\_staging\brian-os-fleet")
$ErrorActionPreference = 'Stop'
$repo = 'C:\Brian\02_Projects\brian-os-fleet'
$py   = Join-Path $env:LOCALAPPDATA 'hermes\hermes-agent\venv\Scripts\python.exe'

New-Item -ItemType Directory -Force -Path $Stage | Out-Null
robocopy "$repo\runtime" "$Stage\runtime" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
robocopy "$repo\tests"   "$Stage\tests"   /MIR /NFL /NDL /NJH /NJS /NP | Out-Null

Write-Host "Staged to $Stage. Running the 52-test suite on the copy..."
$env:PYTHONUTF8 = '1'
$out = "$Stage\_staging_test.out"
# Start-Process gives a clean exit code (a piped 2>&1 would mask python's and treat
# stderr warnings as errors).
$p = Start-Process -FilePath $py -ArgumentList '-m','unittest','discover','-s','tests' `
        -WorkingDirectory $Stage -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError "$out.err"
$code = $p.ExitCode
Get-Content $out, "$out.err" -ErrorAction SilentlyContinue | Select-String -Pattern '^Ran |^OK|^FAILED'

if ($code -eq 0) { Write-Host "`nSTAGING OK - tests pass on the copy; safe to deploy to live (deploy_fleet.ps1)." }
else { Write-Host "`nSTAGING FAILED (exit $code) - DO NOT deploy; fix first." }
exit $code

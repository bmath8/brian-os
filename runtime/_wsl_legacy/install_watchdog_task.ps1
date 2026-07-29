# Registers the Windows-side fleet watchdog: runs fleet_keepalive.ps1 at logon and
# every 3 minutes, even on battery / during Modern Standby, so a dead WSL/gateway is
# revived within minutes WITHOUT a re-logon. Idempotent (-Force).
$ps1 = 'C:\Brian\02_Projects\brian-os-fleet\runtime\fleet_keepalive.ps1'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f $ps1)
$tLogon  = New-ScheduledTaskTrigger -AtLogOn
$tRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 3) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 4) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId ("{0}\{1}" -f $env:USERDOMAIN, $env:USERNAME) `
    -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'BrianOS-FleetWatchdog' -Action $action `
    -Trigger $tLogon, $tRepeat -Settings $settings -Principal $principal -Force | Out-Null
Write-Output 'Registered BrianOS-FleetWatchdog:'
Get-ScheduledTask -TaskName 'BrianOS-FleetWatchdog' | Select-Object TaskName, State | Format-Table -AutoSize

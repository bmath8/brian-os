' Launch the Hermes gateway under a HIDDEN console (Run window style 0) so ALL of its
' child processes - the cron scripts AND the Photon iMessage node sidecar - inherit a
' hidden console and never pop a visible window on Brian's screen.
'
' Why this fixes the popups: the old launch used pythonw.exe, which has NO console at
' all. On Windows, a console child (python.exe / node.exe) spawned by a parent that has
' no console is given its OWN new console window -> the flashing terminals. Running the
' gateway as python.exe inside a hidden console means children attach to that hidden
' console instead, so nothing shows.
Dim sh, py
Set sh = CreateObject("WScript.Shell")
py = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\hermes\hermes-agent\venv\Scripts\python.exe"
sh.Run """" & py & """ -m hermes_cli.main gateway run", 0, False

' BrianOS keepalive launcher — starts the hidden every-3-min keepalive loop at logon.
' No console window (0 = hidden). Lives in the Startup folder.
CreateObject("WScript.Shell").Run "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""C:\Brian\02_Projects\brian-os-fleet\runtime\fleet_keepalive_loop.ps1""", 0, False

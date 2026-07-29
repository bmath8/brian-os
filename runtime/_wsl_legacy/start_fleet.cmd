@echo off
REM Brian OS fleet launcher (runs at logon via BrianOS-Fleet.vbs).
REM 1) ensure Ollama is up + bound to 0.0.0.0   2) ensure the Hermes gateway is up.
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Brian\02_Projects\brian-os-fleet\runtime\ensure_ollama.ps1"
wsl -d Ubuntu -u mathe -e bash /home/mathe/.hermes/start_gateway_if_down.sh

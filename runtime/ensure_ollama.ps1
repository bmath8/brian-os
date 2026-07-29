# Ensure Ollama is running. NATIVE-WINDOWS version (2026-07-06):
# - Binds to localhost ONLY. The old 0.0.0.0 bind was a WSL-era requirement and
#   exposed the unauthenticated Ollama API to the whole LAN. Native Hermes reaches
#   it at 127.0.0.1:11434. (If the WSL fallback is ever revived, set OLLAMA_HOST
#   back to 0.0.0.0 deliberately - see host-architecture-decision.)
# - "ollama app.exe" is the tray app (no console window pops).
# Idempotent. Called at logon and by keepalive/watchdog.
$ok = netstat -ano | Select-String ':11434' | Select-String 'LISTENING'
if (-not $ok) {
    Get-Process ollama* -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    Start-Process "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"
    Start-Sleep -Seconds 8
    "ensure_ollama: restarted (localhost bind)"
} else {
    "ensure_ollama: already healthy"
}

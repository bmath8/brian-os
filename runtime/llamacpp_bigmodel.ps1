# llamacpp_bigmodel.ps1 - tuned llama.cpp server for qwen3:30b-a3b (BIG_MODEL).
#
# MEASURED 2026-07-11 (RTX 4070 SUPER 12GB, identical 300-token prompt):
#   Ollama 0.31.1:                    39.5 tok/s
#   llama-server --n-cpu-moe 32:      34.5 tok/s   (too many experts on CPU)
#   llama-server --n-cpu-moe 22:      43.8 tok/s   (+11% vs Ollama; VRAM 11.9GB - zero headroom)
#
# VERDICT: +11% does NOT meet the 1.5x adoption bar - the fleet stays on Ollama
# (one serving stack, VRAM headroom for daytime apps). Revisit if:
#   - an Ollama update regresses MoE speed (watch currency_agent's ollama release flags), or
#   - RAM upgrade lands (bigger models where llama.cpp's expert-placement control matters), or
#   - a fleet task becomes throughput-bound at 2am (no VRAM contention then).
#
# Usage: powershell -File runtime\llamacpp_bigmodel.ps1    # serves OpenAI-compatible API on :8081
#        then point a client at http://127.0.0.1:8081/v1 (model name is ignored by llama-server)
# Binaries: C:\Brian\tools\llamacpp (b9965, CUDA 12.4). Reuses Ollama's GGUF blob - no re-download.
$blob = (ollama show qwen3:30b-a3b --modelfile 2>$null | Select-String '^FROM' | Select-Object -First 1) -replace '^FROM\s+',''
if (-not $blob -or -not (Test-Path $blob.Trim())) { Write-Error 'qwen3:30b-a3b blob not found (ollama pull it first)'; exit 1 }
Write-Host "Serving $($blob.Trim()) on http://127.0.0.1:8081 (stop Ollama's big model first: ollama stop qwen3:30b-a3b)"
& C:\Brian\tools\llamacpp\llama-server.exe -m $blob.Trim() --n-gpu-layers 99 --n-cpu-moe 22 `
    --flash-attn on -c 12288 --port 8081 --host 127.0.0.1

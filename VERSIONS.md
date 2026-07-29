# Pinned versions — known-good fleet stack (#9)
_Last verified 2026-06-22. Update deliberately, on a copy — never blind-update a working fleet._

| Component | Pinned / known-good | Notes |
|---|---|---|
| Hermes Agent | **v0.17.0** (2026.6.19, upstream **d6269da7**) | native Windows; gateway + cron + Telegram + iMessage(photon). In-place updated 2026-06-25 (was 5f55f0ff/72bfc48; pulled to origin/main d6269da7, divergence cleared) - verified: hermes_cli OK, config v30, gateway+keepalive up, brief delivers. |
| Ollama | **0.30.10** | runs models 100% on GPU (RTX 4070 SUPER, 12 GB) |
| Local model (default) | **qwen3:8b** | daily driver, ~5.6 GB VRAM, fits with desktop up |
| Escalation model | **qwen3:14b** | income-critical drafts; VRAM-gated, off-peak |
| Critic model | **deepseek-r1:14b** | overnight-worker critic |
| Embeddings | **nomic-embed-text** | RAG index |
| Python (venv) | 3.11 | `%LOCALAPPDATA%\hermes\hermes-agent\venv` |

## Update rule (do NOT blind-update)
1. A prior auto-update broke the fleet once. **Disable Ollama auto-update** in the Windows Ollama app settings (System tray → Settings → uncheck auto-update), and don't run `hermes update` against the live install.
2. To update: install to a COPY / second dir, run the 52-test suite + a manual brief, confirm `ollama ps` stays `100% GPU`, then cut over. Roll back with `deploy_fleet.ps1 -Rollback` (scripts) or by repointing to the prior install.
3. Record the new known-good versions here after a successful cutover.

## Quick verify
```
hermes --version
(Invoke-RestMethod http://localhost:11434/api/version).version
ollama list   # qwen3:8b, qwen3:14b, deepseek-r1:14b, nomic-embed-text
```

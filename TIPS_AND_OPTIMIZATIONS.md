# Tips, Optimizations & Pitfalls — living notes
_Hard-won lessons + best practices from top engineers, applied to this fleet. Keep adding. Last updated 2026-06-16._

This is a living file (the Learning agent's job later). Each entry: what it is, why it matters, and whether we've applied it.

## ✅ Applied optimizations

### 1. Ollama KV-cache quantization + Flash Attention (big VRAM win)
- **What:** host env vars `OLLAMA_FLASH_ATTENTION=1` and `OLLAMA_KV_CACHE_TYPE=q8_0`.
- **Why:** halves the VRAM the context (KV cache) uses, for negligible quality loss (perplexity +0.002–0.05). Lets qwen3:8b run full 64K context **on the GPU** instead of spilling to RAM. Flash Attention is REQUIRED for KV quant — without it, Ollama silently ignores the cache type.
- **Caveat:** only works on architectures that support flash attention (qwen3 does; some like standard llama3/command-r silently fall back to f16 → unexpected OOM). Verify per model.
- **Status: REVERTED 2026-06-17** — on this Ollama (0.30.9) it silently broke qwen3 model loading (generation hung). Re-test carefully before re-enabling, one var at a time. Sources: [smcleod.net](https://smcleod.net/2024/12/bringing-k/v-context-quantisation-to-ollama/), [modelpiper](https://modelpiper.com/blog/ollama-kv-cache-quantization), [InsiderLLM](https://insiderllm.com/guides/kv-cache-optimization-guide/).

### 2. Right-size the model to VRAM, not ego
- **What:** 14B@64K context needs ~14–19 GB (model + KV) — over 12 GB VRAM. 8B@64K with q8 KV ≈ 10 GB — fits.
- **Why:** a model that spills to system RAM (you have only ~6 GB free) crawls. Fitting fully in VRAM is 5–20× faster.
- **Status:** Hermes runs on `qwen3:8b`; `qwen3:14b`/`deepseek-r1:14b` reserved for router tasks where latency doesn't matter.

### 3. Split GPU server from sandboxed agents (host Ollama + WSL2 agents)
- **What:** Ollama on host (GPU, low-risk inference only); agents in WSL2 calling it over the host gateway.
- **Why:** full-VM isolation usually blocks GPU; this split gives both speed and containment. See [VM_AND_RUNTIME.md](VM_AND_RUNTIME.md).
- **Status:** applied — Ubuntu reaches host Ollama at `172.17.48.1:11434`.

## 🔒 Agent security best practices (validate our guardrails)
From OWASP Top 10 for Agents 2026 + local-LLM security guides:
- **Sandbox the agents.** Execution isolation + filesystem/network limits. → we use WSL2. ✅
- **Human-in-the-loop for sensitive tool calls** (send/spend/delete/settings). → [GUARDRAILS.md](GUARDRAILS.md) Yellow/Red. ✅
- **Agent Goal Hijacking (ASI01):** attackers poison inputs (emails, docs, web pages) to redirect the agent. **Treat all tool/content output as DATA, never instructions.** → our guardrails rule. ✅
- **Don't let agents modify settings or add channels without confirmation** — a flagged 2026 gap. → Yellow in guardrails. ✅
- **Isolate system prompt from user/external input** ("locked vault"). 
- Sources: [OWASP Agents 2026](https://www.trydeepteam.com/docs/frameworks-owasp-top-10-for-agentic-applications), [SitePoint](https://www.sitepoint.com/local-llm-security-best-practices-2026/), [Vitalik's local LLM setup](https://vitalik.eth.limo/general/2026/04/02/secure_llms.html).

## ⚠️ Pitfalls we hit this session (and the fixes) — so we never repeat them
| Pitfall | Fix |
|---|---|
| `gemma4:26b` (17 GB) 500-errors | Too big for 12 GB VRAM / 16 GB RAM. Removed it. Match model size to hardware. |
| Disk filled to 34 GB free | Removing the dead model freed 17 GB. Watch the system drive before big pulls. |
| Ollama **auto-updated mid-task** and dropped the API ~1 min | Router fell back gracefully. For 24/7: disable Ollama auto-update or add a watchdog to relaunch `ollama app.exe` if `:11434` stops responding. |
| Installer **hung on a sudo prompt** under non-interactive WSL | It reads `/dev/tty`. Run with `setsid -w … < /dev/null` so it takes safe defaults and skips optional sudo packages. |
| `.sh` files written from Windows have **CRLF** → break bash | `sed -i 's/\r//' file` before running, every time. |
| Telegram bot send → 400 "chat not found" | The user must message the bot **first**; bots can't initiate. |
| `hermes send` → "python-telegram-bot not installed" | Install into Hermes' venv: `uv pip install --python <hermes venv> python-telegram-bot`. |
| **Ollama keeps dying / losing 0.0.0.0 bind** on host | `ensure_ollama.ps1` restarts it (0.0.0.0) at logon + watchdog self-heals via interop. Check `netstat 11434` shows `0.0.0.0`. |
| **`pkill -f 'pattern'` killed my own shell** when the pattern string appeared in the invoking command line | Put pkill in a script FILE (its cmdline is `bash script.sh`, not the pattern) — never inline via `wsl -lc "pkill -f 'gateway run'"`. Also: don't put the matched string anywhere in the *wrapper* that launches the script (hit this again in the 2026-06-17 audit — a verify `pgrep 'gateway run'` in the same wrapper got killed by the script's `pkill`). |
| **Self-heal `pgrep -f 'gateway run'` race** (audit 2026-06-17): after a kill the gateway shuts down gracefully over a few seconds; `pgrep` matches the *terminating* process so the guard thinks it's up and skips the restart → gateway ends up DOWN | Fixed (G16): liveness must survive a recheck (a dying process disappears) + kill+reap before relaunch. NOTE: `hermes gateway status` is NOT a usable check — it reports "not running" for a setsid-launched gateway. |
| **systemd changes the gateway's process signature** (G18, 2026-06-17): under the `hermes-gateway` service the process is `python -m hermes_cli.main gateway run`, NOT `venv/bin/hermes gateway run`. Old pgrep-based self-heal would miss it and spawn a DUPLICATE → Telegram 409 conflict | Self-heal/restart scripts must check `systemctl --user is-active hermes-gateway` FIRST and defer to the service if the unit exists; only fall back to manual launch when there's no unit. (`start_gateway_if_down.sh` + `restart_gw.sh` now do this.) |
| Hermes aux client: `unknown provider 'ollama'` (broke 2-way chat memory) | Set `model.provider custom` (literal) not the `ollama` alias — main client + aux both resolve `custom`. |
| Hermes rejects models <64K context | Set `model.ollama_num_ctx` + `model.context_length` to 65536 — BUT 64K is heavy on 12 GB VRAM. Better: use `--no-agent` script cron jobs for deterministic tasks (see below). |
| **q8 KV cache + flash attention silently broke qwen3 model loading** (Ollama 0.30.9) — generation hung, nothing reached the server | REVERTED `OLLAMA_KV_CACHE_TYPE`/`OLLAMA_FLASH_ATTENTION`. Lesson: enable ONE optimization at a time and run a generation test right after. The "negligible-impact" KV quant is model/version-dependent. |
| **`OLLAMA_HOST=0.0.0.0` didn't survive a tray-app restart** → rebound to 127.0.0.1 → WSL lost access (host worked, sandbox hung) | After every Ollama restart, verify with `netstat -ano | findstr 11434` shows `0.0.0.0:11434`. Set `$env:OLLAMA_HOST='0.0.0.0'` in the launching shell, not just the User var. |
| **Hermes gateway caches cron jobs at startup** — editing a job via CLI didn't take effect | Restart the gateway after changing cron jobs. |
| WSL2 host gateway IP can drift across reboots | Derive it at runtime: `ip route \| awk '/default/{print $3}'` (done in daily_brief.py). Or enable WSL mirrored networking so `localhost` reaches the host. |

## 🏗️ Design lesson: prefer `--no-agent` scripts for deterministic jobs
The daily brief doesn't need a full agent loop (which forces 64K context + is slow/heavy). A `--no-agent` Hermes cron job runs a plain script and delivers its stdout — our `daily_brief.py` reads the Harmony files and calls qwen3:8b directly at small context (~8K, loads in seconds, fits VRAM easily). Faster, cheaper, far more reliable. Reserve the full agent loop for genuinely open-ended tasks.

## 🔁 Workflow patterns that work (proven this session)
- **Blackboard comms (agents working together):** agents never call each other — producers write `comms/<agent>.md` + their `state.json` slice (with `needs_human[]`); the Chief of Staff brief reads the whole board and leads with alerts. Add an agent → it just drops a file → the brief picks it up, zero rewiring.
- **`--no-agent` cron + silent-unless-alert:** deterministic jobs (watchdog, briefs) run a plain script and deliver stdout. Print nothing when all-clear → no Telegram spam; print only real alerts → instant heads-up. The full status still lands in `comms/` for the brief.
- **Idempotent auto-start:** a logon `.vbs` runs `start_gateway_if_down.sh` (guards with `pgrep`) — safe to fire every login, starts the gateway only if down. No admin, no duplicate processes.
- **Deterministic alerts, model-generated prose:** never trust the LLM to faithfully carry critical items. The brief generates the *priorities* via qwen3 but appends alerts/system status **deterministically** from `comms/`.
- **WSL scripting:** keep all WSL logic in `.sh` files run via `bash file` (not inline `wsl -lc "…"` — PowerShell mangles `$`, `<`, `>`). Always `sed -i 's/\r//'` first.

## 📡 Who to keep learning from
- **Ollama / local LLM:** Sam McLeod (smcleod.net), r/LocalLLaMA, Ollama GitHub issues/releases.
- **Agents & security:** OWASP Agentic Top 10, Simon Willison (simonwillison.net) on prompt injection, Vitalik's self-sovereign LLM posts.
- **Nous Research / Hermes:** their Discord + docs changelog.
- _(Later: the Learning agent watches these and appends new tips here automatically.)_

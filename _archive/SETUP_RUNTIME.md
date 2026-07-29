# Runtime Setup — WSL2 + Host Ollama + Hermes/OpenClaw + Telegram
_Step-by-step. 🟢 = I can run it for you · 🔵 = needs you (admin, reboot, or a token). Last updated 2026-06-16._

## Goal
Agents run sandboxed in WSL2; they call **Ollama on the host** (GPU) over the network; they message you on **Telegram**. Local models first, per ROUTING.

---

## Step 1 — Expose host Ollama to the sandbox  🔵 (one setting + restart Ollama)
By default Ollama listens on `127.0.0.1`, which WSL2 **cannot** reach. Fix once:
1. Set a user environment variable: `OLLAMA_HOST = 0.0.0.0` (Windows: Settings → System → About → Advanced system settings → Environment Variables → New, under your user).
2. Quit Ollama from the system tray and reopen it (so it rebinds).
3. Verify it's listening broadly (PowerShell): `netstat -ano | findstr 11434` → should show `0.0.0.0:11434`.

> Security note: `0.0.0.0` exposes Ollama to your local network. Fine on a trusted home network; if you want it tighter later, bind to the WSL gateway IP instead.

> ⚠️ **Ollama auto-updates and briefly drops the server** (seen 2026-06-16: it updated to v0.30.9 mid-task and the API went offline for ~1 min). The router handles this gracefully (flags escalation, no crash). For the always-on runner, either disable Ollama auto-update or have a watchdog restart `ollama app.exe` if `:11434` stops responding.

## Step 2 — Enable WSL2 + Ubuntu  🔵 (admin + reboot)
In an **admin** PowerShell:
```
wsl --install -d Ubuntu
```
Reboot when prompted. First launch asks you to create a Linux username/password (keep it — it's your sandbox login, separate from Windows).

## Step 3 — Confirm the sandbox reaches host Ollama  🟢 (I verify)
Inside Ubuntu, the host is reachable at the WSL gateway. Test:
```
curl http://$(ip route | awk '/default/ {print $3}'):11434/api/tags
```
Should return your model list (llama3, qwen3, deepseek-r1). I'll wire this host IP into the router's `OLLAMA_URL`.

## Step 4 — Get a Telegram bot token  🔵 (2 minutes, you)
1. Open Telegram, message **@BotFather** → `/newbot` → name it (e.g. "Brian OS").
2. Copy the **token** it gives you.
3. Message your new bot once (say "hi") so it can reach you, and get your chat id from **@userinfobot**.
Give me the token + chat id (or paste them into `sandbox/.env` yourself — never commit them).

## Step 5 — Install Hermes (first runtime)  🟢 (I run, you approve prompts)
Inside WSL2: install Hermes Agent per its docs, configure it to:
- use host Ollama as the model backend (the Step-3 URL),
- connect the Telegram bot (Step-4 token),
- load the daily-brief as a cron job (natural-language: "every day at 7am, run the Chief of Staff brief and send it to me").
The brief prompt is ready in [prompts/daily_briefing_agent.md](prompts/daily_briefing_agent.md).

## Step 6 — Retire the interim Claude schedule  🟢
Once Hermes sends the brief reliably, disable the Claude scheduled task `fleet-chief-of-staff-daily-brief` (or keep as a backup). The briefing now runs **locally + free** and pings your phone.

## Step 7 — Add OpenClaw (phase 2)  🟢🔵
Install OpenClaw in the sandbox for browser-heavy jobs (Job Hunter). Same Ollama backend, same Telegram. Wire the Job Hunter prompt next.

---

## What lives where
- **Host:** Ollama (+ GPU), this git repo, the Claude interim schedule.
- **Sandbox (WSL2):** Hermes, OpenClaw, their `.env` (tokens — never committed), the running agents.
- **Shared:** the fleet repo is reachable from WSL2 at `/mnt/c/Brian/02_Projects/brian-os-fleet`.

## Credentials rule (reminder)
Tokens/keys go in `sandbox/.env` inside WSL2, gitignored, never in the host password manager and never committed. Yellow/Red actions in [GUARDRAILS.md](GUARDRAILS.md) still need your approval even though the agent is sandboxed.

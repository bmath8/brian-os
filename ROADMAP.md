# Fleet Roadmap
_Build order. Each agent copies agent #1's shape. Last updated 2026-07-15 (reconciled to 25 live cron jobs)._

> ⚠ **Partly historical** — written during the WSL build. The fleet is now **native Windows** with all agents + 8 skills shipped. See **[CURRENT_STATE.md](CURRENT_STATE.md)** and **[MASTER_STATUS.md](MASTER_STATUS.md)** for current status.

## ✅ Phase 0 — Foundation (2026-06-16)
- [x] Dedicated project + scaffold (`agents/ prompts/ shared/ comms/ logs/ runtime/`)
- [x] Blueprint, Guardrails, Routing
- [x] **Chief of Staff** spec + prompt

## ✅ Phase 0.5 — Local runtime + comms (2026-06-17)
- [x] Local models on GPU (qwen3:8b default; qwen3:14b + deepseek-r1:14b for post-RAM) + free-first router
- [x] Hermes Agent in WSL2, wired to local Ollama (qwen3:8b)
- [x] Telegram channel (two-way)
- [x] Daily brief = `--no-agent` cron → Telegram, 7am
- [x] Blackboard comms; agents → `comms/` → brief aggregates
- [x] **Gateway = systemd `--user` service + linger** — REAL reboot survival confirmed (G2/G18)
- [x] Self-heal hardened + systemd-aware (G16); audit trail in `run_log.md`

## ✅ Phase 1 — The agent set (2026-06-17)
Nine scheduled agents, all local/free on qwen3:8b:
- [x] **Chief of Staff** (daily brief, 7am) — leads with deterministic job-hunt numbers + needs/review + Money&Health + System/RAM + Recall
- [x] **System Watchdog** (4h) — disk/RAM/Ollama/gateway/backup; self-heals; alerts on change
- [x] **Overnight Worker** (2am) — queue → draft→self-verify→revise → review (drafts only)
- [x] **Learning** (6:45am) — recall questions from fleet lessons
- [x] **Finance** (6:50am) — runway + credit from Harmony trackers (never invents numbers)
- [x] **Health** (6:52am) — consistency nudges from Harmony tracker (never invents data)
- [x] **Weekly Review** (Sun 5pm) — funnel + week rollup → Harmony 02_Weekly_Reviews + Telegram
- [x] **Scout** (6:40am) — free DuckDuckGo discovery of fresh listings for target roles → brief (stdlib, no key, no cost)
- [x] **Harmony Backup** (1:30am) + **Model Review** (monthly) — infra/maintenance agents

## ▶ Next (needs Brian or hardware)
- [ ] **Fill tracker data** (Brian) — monthly expenses (→ real runway), health weekly log, job applications. Highest leverage; turns nudges into real status.
- [ ] **64 GB DDR5 RAM** (optional) — more VRAM headroom for bigger local models. Model gating already lives in `fleet_common.model_for()` (VRAM-based); the old `safe_model.py` RAM-gate was retired 2026-07-15 (dead + WSL-path bug).
- [ ] **Vercel Eve job-application agent** — do-together build (Node ≥24 via nvm + Vercel login). Scaffold ready in `eve-eval/`. Portfolio + income.
- [ ] **Job Hunter agent** (future) — only if Brian wants fleet-side job sourcing; AI Job Hunter app already covers tailoring. Draft-only per Guardrails.
- [x] **Scout agent** — DONE (daily, free DuckDuckGo discovery into the brief).

## Phase 2 — Always-on / scale (per NORTH_STAR.md)
- [ ] Move orchestrator to a dedicated always-on box / cloud / serverless (Eve is one path) once income allows.
- [ ] Web dashboard over `comms/` (today: `runtime/fleet_status.sh` gives a CLI snapshot).

## Definition of done for any agent
Spec in `agents/`, runnable script in `runtime/` (mirrored to `~/.hermes/scripts/`), writes a `comms/*.md` + `state.json` slice, has a schedule, respects [GUARDRAILS.md](GUARDRAILS.md), logs its run to `logs/run_log.md`.

# North Star — a 24/7 fleet that works while you sleep
_Honest, staged path from tonight's setup to always-on agents. Last updated 2026-06-17._

> ⚠ **Partly historical** (WSL-era). Stage 1 (always-on, self-healing) is **done natively on Windows**. The remaining north star = a dedicated always-on box (mini-PC) when income allows. See **[CURRENT_STATE.md](CURRENT_STATE.md)**.

## The honest framing first
- **"Build my projects while I sleep"** — realistic, with guardrails: agents research, draft, code, and test overnight, then **queue results for your morning review**. Not unsupervised shipping. You approve anything that sends/deploys/spends/deletes.
- **"Always learning & adapting"** — real: persistent memory + a Learning agent that writes/improves skills from outcomes. It compounds slowly, not magically.
- **"Making me money"** — the honest version: agents **accelerate the activities that make YOU money** (job apps, outreach, content, shippable projects). Fully-autonomous money-making is mostly hype and risk. The win is a **flywheel**: agents save you hours → you earn → you reinvest in better hardware/agents → they do more.

## The four requirements for 24/7
1. **Always-on host** — a machine that never sleeps. (Your laptop sleeping is the #1 blocker today.)
2. **Self-healing services** — things restart themselves; a watchdog notices failures. (We have the watchdog + logon auto-start; not yet a true service.)
3. **Persistent memory + learning loop** — agents remember and improve. (Hermes has memory + skill self-creation; the Learning agent will drive it.)
4. **Safe autonomy** — a task queue agents pull from + guardrails + a morning review gate. (Guardrails done; queue + review gate not yet.)

## Staged path (cheap now → scale with income)
### Stage 1 — Always-on, on what you own (this week, ~$0)
- Set Windows to **never sleep** (plugged in) → power settings. This alone makes the current fleet run overnight.
- Keep the gateway up (logon auto-start, done) + Watchdog (done).
- **Gap to close:** verify it survives a reboot; make the gateway a real auto-restarting service.
- Result: briefing + watchdog + any agent runs 24/7 while the PC is on.

### Stage 2 — Dedicated always-on box (at first income, ~$5–40/mo or ~$200–400 once)
- Move the agent layer to something that's *always* on and not your daily laptop:
  - **Cheap cloud VM** ($5–20/mo) — simplest always-on; or
  - **Used mini-PC / SFF** (~$200–400 once) — local, private, one-time cost; or
  - **Serverless** (Modal / Daytona — Hermes supports both) — hibernates when idle, near-zero cost, wakes for tasks.
- Local heavy models stay on your PC (or rent GPU hours for big jobs); the orchestrator lives on the always-on box.
- **64 GB RAM upgrade** on your PC here too (your #1 bottleneck) so it can run 14B + tools without thrashing.

### Stage 3 — The overnight worker (a few weeks of iteration)
- **Task queue**: a `comms/queue/` of jobs you drop in (or agents generate). Overnight, a Builder agent pulls jobs, works in an isolated git worktree, tests, and writes results + a diff to `comms/review/`.
- **Morning review gate**: your brief leads with "Built overnight — approve?" items. You approve; it merges/ships. Nothing irreversible happens without you.
- Add specialized agents (each owns a goal) all coordinating via the blackboard we built.

### Stage 4 — Self-improving (ongoing)
- Learning agent reviews what worked/failed, updates skills + memory, proposes its own improvements for your approval.
- The fleet adapts to your life because every outcome feeds back into memory.

## What's already done toward this (tonight)
Local models on GPU · free-first router · resource-aware model gating · Hermes in a sandbox · Telegram · daily brief · agent-to-agent blackboard comms · System Watchdog · logon auto-start · guardrails · a living lessons + gaps log.

## The next 3 concrete moves
1. **Set Windows to never sleep** (you, 1 min) — unlocks overnight running today.
2. **Make the gateway a self-restarting service** + verify reboot survival.
3. **Build the task queue + morning review gate** (Stage 3 core) — this is the "works while I sleep" engine.

> Reality check (Charter principle): every stage must earn its complexity. Don't build Stage 3 before Stage 1 is rock-solid. Cheap, reliable, and compounding beats ambitious and fragile.

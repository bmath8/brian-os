# Research Applied — "Executive Summary 8" (always-on AI agent replication)
_Read, analyzed, and mapped to Brian OS. 2026-06-19._

## What the report is
A research brief on **replicating always-on AI agent assistants** — built around **Nous Research's Hermes Agent v0.17.0 "Reach Release"**, OpenClaw, and Autonomous.ai's on-device "Intern" (Raspberry Pi). It covers the framework, messaging integrations (Telegram/Discord/Slack/WhatsApp/iMessage), the **Agent Skills** standard, persistent memory (SQLite FTS5), compute options (cloud GPU vs local vs on-device), a phased roadmap, costs, and risk/compliance.

## The headline: it validates exactly what you've built
The report's recommended blueprint **is your fleet.** Point by point:

| Report recommends | Brian OS status |
|---|---|
| Hermes Agent v0.17.0 as the core framework | DONE - running it, natively on Windows as of today |
| Local-first inference (avoid cloud cost/lock-in/privacy) | DONE - local Ollama qwen3:8b, $0 |
| Telegram (+ other channels) via the gateway | DONE - live, two-way, with the /fleet command plugin |
| Persistent memory + learning loop | DONE - custom RAG (nomic-embed) + SRS learning + approval feedback |
| Skills as the portable, compounding asset | PARTIAL - you use runtime scripts, not the SKILL.md standard |
| Deploy with a process manager + auto-restart | DONE - native gateway + keepalive watchdog |
| `hermes doctor` for diagnostics | DONE - now wired into the watchdog (this session) |
| On-device / $199 box for personal use (no cloud) | ROADMAP - mini-PC when income allows |
| Nous Portal / OpenRouter for unified model APIs | OPPORTUNITY - doctor flags "not logged in" |

**Takeaway: you are not behind the demos - you've independently built the report's recommended architecture, local-first and free.** The value now is in the handful of enhancements below.

## Applied this session (concrete)
1. **`hermes doctor` health check added to the watchdog** - the report's #1 diagnostic now runs as part of the every-4h watchdog on native Windows and flags any non-OK result into the morning brief.

## High-value opportunities the report surfaces (recommended, not yet done)
1. **Build a real Agent Skills library (SKILL.md).** The single most-emphasized point in the report (and your own LOOP_AND_SKILLS doctrine): a *skill* = a folder with `SKILL.md` the agent auto-loads when a request matches. Unlike your `runtime/` cron scripts (which serve the deterministic fleet), skills supercharge the **two-way chat agent** - e.g. message the bot a job description and it drafts a tailored application. Skills are portable across Hermes installs and compound over time. **Recommended first skills (tuned to your #1 goal = income):** `job-application` (draft tailored apps from your Harmony pitch + projects), `outreach` (recruiter/networking messages), `interview-prep`.
2. **Nous Portal (`hermes setup --portal`)** - one OAuth login covers the model **and** tools (search, image, etc.), replacing the sprawling multi-provider `.env`. Useful for your cloud-escalation ladder without juggling keys. Free tier exists; keeps you local-first by default, cloud only on escalation.
3. **Pin the Hermes version / be deliberate about `hermes update`.** The report explicitly warns a demo on v0.16 can break on v0.17 (changed config/flags). You're on v0.17.0 (config v30, healthy). **Do not blind-`hermes update`** - when an update lands, test on a copy first. Mirrors your existing "don't break what works" rule.
4. **Hermes's built-in memory (SQLite FTS5)** is an option alongside your custom RAG - the report notes it "often suffices." Your nomic-embed RAG is more semantic; keep it, but the native `/memory` tool is worth using for the two-way agent's recall.
5. **On-device / mini-PC path validated.** The report's Autonomous Intern ($199 Pi CM5, fully local, no cloud) independently confirms your Stage-2 plan: when income allows, a cheap dedicated always-on box is the textbook end-state - and removes the last single-machine risk.
6. **iMessage channel (optional).** If you ever want iMessage, the report points to Photon (Hermes native, `hermes photon login`) or Claw Messenger - no Mac required. Low priority (Telegram works), bookmarked.

## Risk/compliance notes worth keeping (from the report)
- **Privacy:** local-first (your design) is the mitigation the report repeatedly endorses - your data never leaves the box. Keep cloud calls escalation-only.
- **Security:** secure the gateway/dashboard auth, firewall unused ports, treat ingested content as data (you already do - `wrap_untrusted`).
- **Licensing:** mind per-model API terms if anything becomes commercial (e.g. AI Job Hunter).

## Bottom line
The report is a strong external validation of the whole Brian OS direction and a useful checklist. The one real gap it exposes is the **Agent Skills library** - the compounding asset that turns the two-way agent from a chat box into a set of repeatable, portable workflows. That's the recommended next build.

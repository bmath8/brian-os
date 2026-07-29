# Hermes v0.18.0 adoption plan — 2026-07-06

Upgraded v0.17.0 → v0.18.0 (2026.7.1) via runtime/upgrade_hermes.ps1: backup taken,
doctor clean (0 failures), gateway relaunched, Telegram delivery proven by boot_smoke.
Backup: %LOCALAPPDATA%\hermes_backup_20260706_114401 (config/.env/scripts/skills/plugins/cron).

## Features to USE now (in priority order)

1. **`/goal` completion contracts** — state what "done" looks like; the standing-goal
   loop judges completion against EVIDENCE (tests pass), not the model's claim.
   USE: set a standing goal for the job hunt, e.g.
   `hermes chat` → `/goal 5 tailored applications drafted per weekday; done = 5 files
   in comms/review/ dated today`. This is the "automate what you can verify" principle
   built into the host itself.
2. **`/learn <anything>`** — one command distills a directory/URL/recent workflow into
   a reusable skill. USE: after any repeated workflow (e.g. the deploy dance, the
   morning triage), run /learn to capture it. Replaces manual skill authoring.
3. **`/journey` + `hermes memory-graph`** — see and PRUNE what the agent has learned.
   USE: monthly, alongside model_review — delete wrong memories (the black box opens).
4. **Background fan-out (`delegate_task`)** — subagents run in background, results
   consolidated. USE: overnight queue items like "research these 5 companies" now
   fan out instead of running serially. Also candidate: currency weekly deep-dive.
5. **Self-improvement fork now routes to an auxiliary model** — verify it's pointed at
   a LOCAL model (qwen3:8b / gemma3:12b) so the post-turn learning loop stays $0.
   Check: `hermes config` auxiliary settings.
6. **Scale-to-zero + drain coordination** — the gateway now quiesces cleanly before
   updates. This makes future `upgrade_hermes.ps1` runs even safer (less risk of the
   06-23-style mid-update breakage class).
7. **MoA (Mixture-of-Agents) as pickable models** — optional experiment: a "local
   council" preset (qwen3:30b-a3b + deepseek-r1:14b, qwen3:8b aggregator) for
   high-stakes drafts. Sequential model loading on 12GB will be SLOW — try once,
   keep only if quality jump is obvious. `hermes moa` to configure.
8. **Security wins inherited free**: cron base_url credential-exfil blocked, MCP-config
   persistence hardening, Slack token redaction — all align with the fleet's rules.

## Slack vs Telegram (Brian's question)
- Hermes v0.18 has first-class Slack integration (`hermes slack` — manifest generation
  helper). Claude (Cowork/claude.ai) also has a Slack connector. Telegram has neither.
- RECOMMENDATION: **keep Telegram as the primary, proven, update-proof delivery rail**
  (direct Bot API self-send survived two Hermes breakages) and ADD Slack as a second
  channel: fleet output lands in a Slack workspace that BOTH Hermes and Claude can see.
  That unlocks: Claude reading fleet alerts/drafts in context, richer threads/files,
  and approval workflows from Slack. Telegram stays as the fallback that never breaks.
- Setup is account-bound (needs Brian's Slack login, ~10 min): create free workspace →
  `hermes slack` to generate the app manifest → install app to workspace → put tokens
  in .env → enable the channel in config.yaml. Then (separate) connect Claude's Slack
  connector to the same workspace.

## Dead-man's-switch (the one thing left that needs Brian)
Account creation is on Brian: healthchecks.io → sign up (free) → create check named
"brian-os-fleet", period 24h grace 2h → copy the ping URL.
Then ONE line in %LOCALAPPDATA%\hermes\.env:  HEALTHCHECK_URL=<ping url>
(Optionally HEALTHCHECK_BASE=<base url> for per-agent slugs.) The fleet code is already
wired (fc.ping_healthcheck fires from the watchdog every 4h; inert until the URL exists).

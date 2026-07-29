# Agent 01 — Chief of Staff (daily-brief)
_The hub. Assembles Brian's one morning brief from every other agent's output. The template the rest of the fleet copies._

- **Owns:** orchestration + daily focus.
- **Why it exists:** Brian needs one place each morning that says "here's your day and what the fleet did," instead of checking twenty things. _Solves:_ scattered context, missed priorities.
- **Cadence:** daily, 7:00 AM → Telegram (cron `daily-brief`, `no_agent` script `daily_brief.py`).
- **Tier/model:** free local `qwen3:8b` (deterministic assembly; the brief is mostly file-read + render, light LLM touch).
- **Script:** `runtime/daily_brief.py` · **Deliver:** self-sends via `fc.telegram_send` (update-proof; cron is `--deliver local`).

## Inputs (reads) — as actually implemented
- `comms/state.json` — each agent's `last_run`, `status`, `needs_human[]` (aggregated as "Needs you").
- `comms/system_status.md` — Watchdog's status line (disk/RAM/Ollama/gateway/backup).
- `comms/resource_status.json` — live RAM/commit line (from `resource_probe.ps1`).
- `comms/recall.md` — Learning agent's 3 recall questions.
- `comms/review/*.md` — overnight worker drafts pending approval.
- `comms/calendar.md`, `comms/career.md`, `comms/gigs.md`, `comms/scout.md`, `comms/currency.md`, `comms/finance.md`, `comms/health.md`, `comms/inbox.md`, `comms/networking.md` — producer sections.
- Harmony `Dashboard.md` for priorities (fallback to `C:\Brian\Harmony_backup\Dashboard.md` if OneDrive wiped the local copy).
- _New producers just drop a `comms/*.md` + a `state.json` slice — the brief auto-picks them up, no rewiring._

## Output (writes)
- `comms/daily_brief.md` (persisted + history in `comms/briefs/`).
- Template lives in `prompts/daily_briefing_agent.md`.
- Updates its slice of `state.json`.

## Escalation
Collects every `needs_human[]` from other agents and lists them under "⚠️ Needs you today" at the top. Anything Yellow/Red per GUARDRAILS is surfaced, never auto-done. The brief now **leads with the apps-vs-target scoreboard** (career agent) so progress is the first thing Brian sees.

## Done-when
Brief generated each morning, reads cleanly in under 60 seconds, every approval-needed item is visible.

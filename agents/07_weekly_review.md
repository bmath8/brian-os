# Agent 07 — Weekly Review
_The Sunday wrap. Compiles the week: job funnel, fleet activity, money/health, learning._

- **Owns:** the end-of-week synthesis Brian reads Sunday evening.
- **Why it exists:** the "fill Friday" funnel review + a week-in-review, done automatically. _Solves:_ forgotten weekly review, losing the long view.
- **Cadence:** Sunday 5:00 PM (cron `weekly-review`, `no_agent` script `weekly_review.py`).
- **Tier/model:** free local `qwen3:8b` for deterministic aggregation + light narrative.
- **Deliver:** writes to Harmony `02_Weekly_Reviews/` + Telegram summary.

## What it does (as implemented)
- Job funnel: deterministic parse of `03_Career/Job_Tracker.md` (applied / responded / interview / offer).
- Fleet activity: pulls `comms/fleet_health.md` (log_analyzer) + run ledger.
- Money/health: pulls `comms/finance.md` + `comms/health.md`.
- Learning: pulls recall/SRS progress.
- Lands after `wiki_agent` (16:45) and `outcome_learner` (16:50) so it can use their output.

## Output (writes)
- Harmony `02_Weekly_Reviews/YYYY-Www.md`.
- Telegram summary.
- `state.json` slice `weekly_review`.

## Done-when
Weekly review posted Sunday; funnel numbers accurate (deterministic, not guessed); long-view items surfaced.

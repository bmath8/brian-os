# Agent 18 — CEO Report
_Brian's monthly investor-update-for-his-own-life._

- **Owns:** the monthly one-pager: cost, what shipped, where it failed, next-month bets.
- **Why it exists:** a cadence to actually review the fleet's ROI and reliability. _Solves:_ "is this thing earning its keep?"
- **Cadence:** 1st of month, 7:30 AM (cron `ceo-report`, `no_agent` script `ceo_report.py`).
- **Tier/model:** free local `qwen3:8b` for ONE narrative paragraph; all numbers deterministic.
- **Deliver:** writes `comms/ceo_report.md` + sends to Telegram + `state.json` slice.

## What it does (as implemented)
- Pulls deterministic stats: agent runs/failures (run_log + trajectory), drafts approved/rejected/pending, git commits (30d), career + outcomes summaries.
- One LLM paragraph: mission (income/job hunt) → reliability → one next-month recommendation.
- Cost line is always "$0 marginal (all local models)."

## Output (writes)
- `comms/ceo_report.md` — persisted.
- Telegram send (via `fc.telegram_send`).
- `state.json` slice `ceo_report`.

## Hard rule
Never invents numbers; report-only (the send is a notification, not an action).

## Done-when
Report lands on the 1st; numbers trace to logs/git; recommendation is one concrete bet.

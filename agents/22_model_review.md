# Agent 22 — Model Review
_Monthly model + security posture review for the local stack._

- **Owns:** the monthly "are our models/security still right?" pass.
- **Why it exists:** models, Ollama, and the threat surface drift; a monthly review catches drift before it bites. _Solves:_ silent config rot, missed security steps.
- **Cadence:** monthly, 1st at 3:00 AM (cron `model-review`, `no_agent` script `model_review.py`).
- **Tier/model:** no model needed for the review itself; may call `hermes security` for posture.
- **Deliver:** writes a review note + Telegram send (via `fc.telegram_send`); `state.json` slice.

## What it does (as implemented)
- Verifies the model set is still the intended one (qwen3:8b default, qwen3:30b-a3b BIG, qwen3-coder:30b code, gemma3:12b vision, deepseek-r1:14b critic, nomic-embed).
- Runs `hermes security` as part of the monthly posture check.
- Flags any model that disappeared, or a config drift from `fleet_common.BIG_MODEL`/`SMALL_MODEL`.

## Output (writes)
- Review note (per `state.json` slice `model_review`).
- Telegram send (notification only).

## Hard rule
Report-only. Never changes model config; raises a flag for Brian to decide.

## Done-when
Monthly review lands; model set reconciled vs fleet_common; security check run.

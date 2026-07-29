# Agent 24 — Feedback
_Brian's weekly "how did the fleet do?" signal → the improvement backlog._

- **Owns:** capturing Brian's feedback on the fleet and turning it into backlog items.
- **Why it exists:** without a feedback loop the fleet can't improve toward what Brian actually wants. _Solves:_ silent misalignment between fleet output and Brian's taste.
- **Cadence:** Sunday 5:00 PM (cron `feedback`, `no_agent` script `feedback.py`) — alongside weekly-review.
- **Tier/model:** free local `qwen3:8b` to phrase; deterministic capture of any feedback Brian left.
- **Deliver:** writes a feedback note + feeds the backlog (`state.json` slice).

## What it does (as implemented)
- Collects any feedback Brian logged during the week (via a command or a flagged brief reply).
- Summarizes sentiment + concrete asks; proposes backlog items (does not auto-implement).
- Surfaces recurring friction so the next improvement pass targets it.

## Output (writes)
- Feedback note (consumed by weekly-review + the improvement backlog).
- `state.json` slice `feedback`.

## Hard rule
Capture + propose only. Never changes the fleet itself; Brian approves backlog items.

## Done-when
Weekly feedback captured; concrete asks turned into proposed backlog items.

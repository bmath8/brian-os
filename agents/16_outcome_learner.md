# Agent 16 — Outcome Learner
_Closes the loop the career agent opens: what actually *worked*?_

- **Owns:** evidence-based application-outcome analysis.
- **Why it exists:** the career agent counts activity (apps sent); this measures *response rate* by role/source/day — so tailoring is evidence, not vibes. _Solves:_ "am I applying to the right things?"
- **Cadence:** Sunday 4:50 PM (cron `outcome-learner`, `no_agent` script `outcome_learner.py`).
- **Tier/model:** free local `qwen3:8b` for ONE recommendation; everything else deterministic.
- **Deliver:** writes `comms/outcomes.md` + `state.json` slice.

## What it does (as implemented)
- Deterministic parse of `03_Career/Job_Tracker.md` pipeline rows.
- Response/interview rate by role-keyword bucket, by source, by day-of-week applied.
- One local-LLM recommendation ("focus here next week, here's the number").
- Below ~5 logged apps: reports "keep logging," no false patterns.

## Output (writes)
- `comms/outcomes.md` — the outcomes readout (consumed by weekly-review + brief).
- `state.json` slice `outcomes` (summary consumed by `ceo_report`).

## Hard rule
Counts only what's logged; never invents numbers.

## Done-when
Outcomes section present when enough data exists; recommendation cites real rates.

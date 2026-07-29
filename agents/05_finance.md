# Agent 05 — Finance
_Life-ops producer. Reads Brian's money trackers and surfaces the picture in the brief._

- **Owns:** the "Money" section of the brief.
- **Why it exists:** one calm weekly/daily money readout instead of spelunking trackers. _Solves:_ scattered finance context.
- **Cadence:** daily, 6:50 AM (cron `finance`, `no_agent` script `finance_agent.py`).
- **Tier/model:** free local `qwen3:8b`; **never invents numbers** (a hallucinated figure was caught in test and fixed — the agent reads trackers and reports, doesn't fabricate).
- **Deliver:** writes `comms/finance.md` + `state.json` slice.

## What it does (as implemented)
- Reads the Harmony finance tracker (`05_Finance/Overview.md`) and any logged transactions.
- Summarizes balances, upcoming bills, burn rate, savings pace.
- Nudges if the tracker is blank (don't guess).

## Output (writes)
- `comms/finance.md` — the Money section source.
- `state.json` slice `finance`.
- `wiki_agent` merges finance notes into `comms/learn/wiki/finance.md`.

## Hard rule
Never sends payments, moves money, or invents figures. Report-only.

## Done-when
Finance section present in the brief; figures trace to a tracker; blank-trackers nudged.

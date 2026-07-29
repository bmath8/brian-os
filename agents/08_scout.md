# Agent 08 — Scout
_Free daily discovery of fresh listings/roles worth Brian's attention._

- **Owns:** the "Scout" section of the brief — surfacing relevant opportunities.
- **Why it exists:** passive discovery of roles/listings Brian would otherwise miss. _Solves:_ blind spots in the job hunt, stale pipeline.
- **Cadence:** daily, 6:40 AM (cron `scout`, `no_agent` script `scout_agent.py`).
- **Tier/model:** **stdlib only** — no API key, no model, no cost. DuckDuckGo + free feeds.
- **Deliver:** writes `comms/scout.md` + `state.json` slice.

## What it does (as implemented)
- Free DuckDuckGo discovery of fresh listings for target roles.
- Deterministic scoring/filtering (keyword fit to Brian's stack).
- Dedup ledger (`comms/.scout_seen.json`) so items surface once.

## Output (writes)
- `comms/scout.md` — the Scout section source.
- `state.json` slice `scout`.
- `wiki_agent` merges scout notes into `comms/learn/wiki/learning.md`.

## Hard rule
Read-only discovery. Never applies, contacts, or drafts — that's the career agent / overnight worker's job.

## Done-when
Scout section present in the brief; new relevant items surfaced; no duplicate spam.

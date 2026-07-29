# Agent 20 — Skill Miner
_Mines Hermes sessions for repeated workflows and DRAFTS new skills._

- **Owns:** the `skills/_drafts/` pipeline — turning Brian's repeated instructions into reusable skills.
- **Why it exists:** the best new skills are your own repeated asks. _Solves:_ re-explaining the same task; skill ideas lost.
- **Cadence:** Sunday 6:30 PM (cron `skill-miner`, `no_agent` script `skill_miner.py`).
- **Tier/model:** free local `qwen3:8b` for drafting; deterministic clustering.
- **Deliver:** writes `skills/_drafts/<slug>/SKILL.md` (review-only) + local run ledger.

## What it does (as implemented)
- Collects user messages from Hermes `state.db` + session request dumps.
- Filters to real instructions (drops code/JSON/error noise), fingerprints intent order-independently.
- Clusters; any workflow asked ≥ `SKILL_MINER_MIN_HITS` (default 3) times → drafts a `SKILL.md` via the local model.
- Dedup ledger so each cluster is drafted once.

## Output (writes)
- `skills/_drafts/<name>/SKILL.md` — **draft only, never auto-installed**.
- `.miner_seen.json` ledger.

## Hard rule
Review-only. Nothing is ever installed as an active skill automatically — Brian moves a draft up to `skills/<name>/` himself.

## Done-when
New repeated workflows drafted for review; no duplicates; nothing auto-activated.

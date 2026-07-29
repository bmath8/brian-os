# Agent 04 — Learning (SRS)
_Turns the fleet's activity into retained knowledge. Spaced-repetition recall builder._

- **Owns:** the spaced-repetition loop — what Brian should remember, and surfacing it for recall.
- **Why it exists:** the fleet should make Brian *smarter*, not just busier. _Solves:_ knowledge decay, "I read that somewhere."
- **Cadence:** daily, 6:45 AM (cron `learning-agent`, `no_agent` script `learning_agent.py`).
- **Tier/model:** free local `qwen3:8b` for card generation/recall phrasing.
- **Deliver:** writes `comms/recall.md` (3 daily recall questions) + the SRS ledger `comms/.srs/cards.json`.

## What it does (as implemented)
- Pulls high-signal facts from the wiki (`comms/learn/wiki/*.md`), career/learn notes, and producer outputs.
- Generates/maintains spaced-repetition cards (Leitner-style intervals).
- Emits 3 recall prompts into the brief each morning (the `learn-and-retain` chat skill feeds the same ledger).
- Feeds `outcome_learner` and `wiki_agent` context.

## Output (writes)
- `comms/recall.md` — the daily 3 questions.
- `comms/.srs/cards.json` — the card ledger (atomic writes).
- `state.json` slice `learning`.

## Done-when
Recall questions present in the brief daily; card ledger advancing; no duplicate/low-value cards.

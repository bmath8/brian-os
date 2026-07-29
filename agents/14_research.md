# Agent 14 — Research (X knowledge base)
_The local, token-FREE processor for the X/Twitter research pipeline._

- **Owns:** turning captured X posts into structured notes in the knowledge base.
- **Why it exists:** Brian feeds X threads into the fleet; this distills them into retained, queryable knowledge (RAG-indexed → brief + /ask). _Solves:_ "I saw something useful on X" → lost.
- **Cadence:** Sunday 6:00 PM (cron `research`, `no_agent` script `research_agent.py`).
- **Tier/model:** free local `qwen3:8b` only (no API cost); dedup ledger so each item is processed once.
- **Deliver:** appends to Harmony `06_Research/X_Knowledge_Base.md` (RAG-indexed) + `state.json` slice.

## What it does (as implemented)
- Reads raw captures from `comms/research_raw/*.json` (written by the paste skill / browser-capture flow).
- Summarizes each via the local model into the AI-handoff template (project tags, key insight, actionable takeaway).
- Low-value items are `SKIP`ped to keep the KB high-signal.
- External post text is wrapped `wrap_untrusted` (a tweet can't hijack the analyst role).

## Output (writes)
- `Harmony/06_Research/X_Knowledge_Base.md` — appended notes.
- `state.json` slice `research`.

## Hard rule
Append-only to the KB; never deletes; never sends the captured content anywhere outbound.

## Done-when
Captured items processed once each; high-signal notes in the KB; low-value skipped.

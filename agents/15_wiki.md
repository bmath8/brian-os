# Agent 15 — Wiki (LLM-wiki memory)
_Compounds knowledge instead of appending forever._

- **Owns:** the living `comms/learn/wiki/*.md` pages.
- **Why it exists:** the fleet's notes are append-only streams; knowledge should *compound* (Karpathy LLM-wiki pattern). _Solves:_ piles of dated notes nobody re-reads.
- **Cadence:** Sunday 4:45 PM (cron `wiki`, `no_agent` script `wiki_agent.py`) — before weekly-review (5:00 PM).
- **Tier/model:** free local `qwen3:8b`; no-op-safe (any failure keeps the existing page).
- **Deliver:** rewrites `comms/learn/wiki/<topic>.md` + `state.json` slice.

## What it does (as implemented)
- For each topic (job-hunt, finance, health, fleet-ops, learning), gathers recent source notes (comms + Harmony trackers).
- Merges new facts in, drops stale/superseded ones — rewrites the page rather than appending.
- The weekly review + `/ask` RAG then draw on a current, compact picture.

## Output (writes)
- `comms/learn/wiki/{job-hunt,finance,health,fleet-ops,learning}.md`.
- `state.json` slice `wiki`.

## Hard rule
No-op-safe: if the model fails, the old page is kept untouched. Never invents facts.

## Done-when
Each topic page current and compact; weekly-review can consume it; no lost prior facts.

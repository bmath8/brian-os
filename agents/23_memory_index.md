# Agent 23 — Memory Index
_Keeps the long-term memory index fresh so /ask and recall find the right notes._

- **Owns:** the index over Harmony notes + fleet knowledge that /ask and the brief draw on.
- **Why it exists:** a memory index rots; Brian's "what did I note about X?" depends on it being current. _Solves:_ "I know I wrote that down but can't find it."
- **Cadence:** daily 1:20 AM (cron `memory-index`, `no_agent` script `memory_index.py`).
- **Tier/model:** no model — deterministic index build (file scan + embed via nomic-embed if used).
- **Deliver:** writes the index artifact the RAG/`/ask` path reads.

## What it does (as implemented)
- Walks Harmony notes + `comms/learn/wiki/*` and rebuilds the lightweight index (titles, tags, mtimes).
- Makes the RAG path (in the chat agent / `/ask`) point at current content.

## Output (writes)
- The memory index artifact (consumed by `/ask` + research).
- `state.json` slice `memory_index`.

## Hard rule
Rebuild-only. Never mutates source notes.

## Done-when
Index reflects last day's edits; `/ask` returns current notes.

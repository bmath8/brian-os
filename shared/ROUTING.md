# Model Routing — Hybrid Balanced
_Which brain does which job. Cheapest tier that succeeds. Last updated 2026-07-15 (routing now via `fleet_common.model_for()`, `safe_model.py` retired)._

## Tiers
| Tier | Models | Cost | Use for |
|---|---|---|---|
| **1 — Local** | Ollama on the RTX 4070 Super. Running: `qwen3:8b` (default), `qwen3:30b-a3b` (BIG, VRAM-gated), `qwen3-coder:30b` (code), `gemma3:12b` (vision), `deepseek-r1:14b` (critic). Reachable at `localhost:11434`. | $0 | Everything routine + most reasoning. Tried FIRST, always. |
| **2 — Cheap cloud** | Haiku 4.5 · GPT-5-mini · Gemini Flash-Lite | ¢ | User-facing but routine: brief assembly, tidy summaries, ranking, short emails. |
| **3 — Frontier** | Sonnet/Opus 4.x · GPT-5.x-Codex · Gemini 3.x Pro | $ | Hard reasoning, final job-application drafts, architecture, anything Brian will send or stake reputation on. |

## Rules
1. **Start one tier below** your instinct; escalate only on a bad result.
2. **Privacy → local.** Anything with personal/financial data prefers Tier 1.
3. **User-facing final output → Tier 2+,** never raw Tier-1 without a cleanup pass.
4. **Log spend.** Every Tier-2/3 call notes est. cost in `logs/run_log.md` so we see when upgrading hardware/plan pays off.
5. **Batch** small tasks into one call instead of many.

## Resource-aware gating (so agents don't thrash)
Model selection runs through **`fleet_common.model_for(task, complexity)`** (in `runtime/fleet_common.py`). It returns the cheapest model that fits the task and the box's live VRAM/RAM, escalating BIG work to `qwen3:30b-a3b` and falling back to `qwen3:8b` under memory pressure. This replaced the old `safe_model.py` (which was dead — hardcoded a WSL path, targeted `qwen3:14b` the router never used, and was called by nothing). The Watchdog still publishes `comms/resource_status.json` as the fleet's live "what can I run right now" signal and alerts (once, on change) when pressure is severe.

**Current reality (16 GB box):** most cron agents call `model_for()` which resolves to `qwen3:8b` by default; BIG tasks use `qwen3:30b-a3b` only when VRAM headroom allows. To change the default (e.g. after a RAM upgrade), set `FLEET_MODEL` / `BIG_MODEL` in **one** place — `fleet_common.py` — not per-agent.

## #1 hardware upgrade (when income allows)
**RAM 16 GB → 64 GB DDR5.** Biggest bottleneck after VRAM — unlocks bigger local models, smoother multi-agent runs, and lets gemma-class models load. Cheap relative to impact. Do this before a GPU upgrade.

## Hybrid in practice (example: Job Hunter)
- Scrape + parse listings → **Tier 1** (local).
- Rank against Brian's profile → **Tier 1/2**.
- Draft the tailored application → **Tier 3** (it's going out with his name on it).

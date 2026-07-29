# Models & Tools Review — 2026-06-17
_Research request: best open models for our rig (GLM-5.2, Kimi, etc.), keep models current, and look at Vercel "Eve". Web-researched June 2026. Sources at bottom._

## The honest headline
The biggest names you asked about — **GLM-5.2 and Kimi K2.7 — cannot run on this machine.** They're frontier-scale Mixture-of-Experts models (Kimi K2.x = **1 trillion** params, ~610 GB; MiniMax M3 = 428B, ~264 GB even at Q4). A reviewer with a **128 GB** mini-PC still can't load M3. Our rig is **12 GB VRAM / 16 GB RAM**. So GLM-5.2 / Kimi belong in our **cloud escalation tier (via API)**, not local. The good news: as APIs they're *cheap* and that's a real upgrade for the fleet's "final, high-stakes" work.

Separately, **Vercel Eve (launched today, June 17 2026)** is a genuinely strong architectural match for what we've built — details at the end.

---

## 1. LOCAL tier (Tier 1, runs free on the 4070 Super, 12 GB VRAM)
**Verdict: keep `qwen3:8b` as the fleet default — it's still the right call for our actual workload** (briefs, summaries, recall, drafts, classification). It has the most reliable tool-calling in its class and fits VRAM with room for context.

What's realistically in reach on 12 GB (7–14B, Q4):
| Model | Fit on 12 GB | Why consider | Verdict for us |
|---|---|---|---|
| **qwen3:8b** (current) | ✅ easy (~5 GB) | Best small all-rounder, top tool-calling | **Keep as default** |
| **qwen3:14b** (have) | ⚠️ tight at 64K ctx | Stronger reasoning | Use **only via `safe_model` gate**; comfortable once 64 GB RAM lands |
| **gemma3:12b** | ✅ Q4_K_M | Strong general + long context | **Worth A/B testing** vs qwen3:8b for the brief |
| **deepseek-r1:14b** (have) | ⚠️ heavy | Hard reasoning, stays local | Keep for latency-tolerant router tasks |
| **gpt-oss:20b** | ⚠️ ~12 GB, OOM-risky | "Adjustable reasoning" hype | **Skip** — scored Tier D (failed) on a real agentic coding test; not worth the OOM risk |
| **devstral-small-2 (24B)** | ❌ needs ~14 GB+ | Best *local* agentic coder | Only after a GPU upgrade |

**Reality check from a June-2026 coding benchmark:** every *local* open model scored Tier C–D on a one-shot "build a full app" test (Qwen 3.5 35B = 55, GPT-OSS 20B = 11/failed). That benchmark is far harder than anything our fleet asks a local model to do — but it confirms: **don't expect a local model to do serious coding.** Route that to cloud.

**The single biggest local upgrade is still the one already planned: 64 GB DDR5 RAM.** It makes `qwen3:14b` the comfortable daily driver. No new model beats that lever on this box.

---

## 2. CLOUD tier (Tier 3 escalation — wire these into `models.json` cloud_fallback)
This is where GLM-5.2 and Kimi actually help us, and they're shockingly cheap. From the June-2026 head-to-head (8-dimension coding rubric, /100):

| Model | Score / Tier | Cost per run | Notes |
|---|---|---|---|
| Claude Opus 4.8 | 95 (A) | ~$1.10 | Frontier; for anything truly high-stakes |
| **Kimi K2.7 Code** | 86 (A) | **~$0.30** | Tier A at ~1/4 the cost — via OpenRouter `moonshotai/kimi-k2.7-code` |
| **GLM 5.2** | 87 (A) | flat **subscription** (Z.ai) | Huge jump from 5.1 (was 46→87); good if you want flat-rate |
| Gemini 3.1 Pro | 82 (A) | ~$0.40 | Fast (14m), cheap Tier A |
| **DeepSeek V4 Flash** | 78 (B) | **~$0.01**, 3 min | Absurd value for "good enough" cloud passes |

**Recommendation:** add a cheap-cloud ladder to our escalation tier — **DeepSeek V4 Flash (¢) → Kimi K2.7 Code / Gemini 3.1 Pro ($) → Opus 4.8 (frontier)**. Get one **OpenRouter** key and we can reach all of them through a single endpoint, keys in `~/.hermes/.env` only (never committed). This upgrades the fleet from "local-only" to "local-first, cheap-cloud-when-it-matters" — exactly the routing doctrine, now with concrete 2026 models.

---

## 3. Vercel **Eve** — worth a serious look
**What it is:** an open-source agent framework (open-sourced by Vercel **June 17 2026**) where **an agent is a directory**: `instructions.md` (system prompt), `tools/*.ts` (one typed tool per file), `channels/*` (Slack / web / API / **cron** / CLI), `connections/*` (typed integrations), `sandbox/*` (isolated compute). Built-in **durable execution, sandboxing, approvals, tracing, and evals**. One codebase deploys to all channels on Vercel Functions. Vercel runs 100+ of their own agents on it.

**Why it's relevant to us:** it mirrors our fleet almost 1:1 — blackboard/agents → directories, GUARDRAILS approvals → built-in approvals, Telegram → channels, cron → cron, our LOOP_AND_SKILLS_DOCTRINE (skills as markdown) → Eve's `instructions.md` + tool files. It directly answers **NORTH_STAR Stage 2** ("move the orchestrator to an always-on box / cloud / serverless").

**The catch:** Eve runs on **Vercel Functions (cloud)** and expects **cloud model APIs** — it doesn't host our local Ollama. So it's not a replacement for the free local tier; it's a **migration/host target** and a **portfolio-grade rewrite** of the orchestration layer.

**Recommendation (staged, not now):** treat Eve as a **Phase-2 evaluation**, not an immediate switch. Two good uses: (a) **portfolio piece** — rebuilding the fleet "the Vercel way" is a strong résumé story alongside AI Job Hunter; (b) **always-on host** — Eve on Vercel for orchestration + approvals + channels, still calling **local Ollama for the cheap/private tasks** (hybrid), cloud APIs for the rest. Do a small spike (one agent, e.g. the daily brief, as an Eve agent) before committing. Don't migrate the working Hermes fleet until Eve is proven and the reliability items (G16/G18) are closed.

---

## 4. "Always update to the best model" — make it a process, not a guess
Add a lightweight **quarterly model review** (a perfect job for the Learning agent later):
1. Re-pull/benchmark 2–3 local candidates that fit 12 GB on a fixed 5-prompt fleet test (brief, summary, recall, draft, classify). Keep the winner as default.
2. Refresh `models.json` cloud_fallback with the current best $/Tier-A picks (today: DeepSeek Flash → Kimi K2.7 → Opus 4.8).
3. Log it in `run_log.md` + `TIPS_AND_OPTIMIZATIONS.md`.
4. Re-evaluate Eve and the RAM-upgrade trigger.

**Immediate, safe actions I can take on your go:**
- Add the concrete 2026 cloud models to `models.json` cloud_fallback (doc-only; no keys, no behavior change).
- A/B test `gemma3:12b` vs `qwen3:8b` for the morning brief and keep whichever reads better.
- Spike one Eve agent (the daily brief) to see the framework hands-on.

I did **not** change any model config — your fleet still runs 100% local/free on qwen3:8b. These are recommendations for your approval.

## Sources
- Best Ollama models June 2026 (Morph): https://www.morphllm.com/best-ollama-models
- Ollama VRAM guide 2026: https://localllm.in/blog/ollama-vram-requirements-for-local-llms
- GPT-OSS 20B hardware: https://willitrunai.com/blog/gpt-oss-20b-vram-requirements
- Kimi K2.6/K2.7 run-locally (Unsloth): https://unsloth.ai/docs/models/kimi-k2.6
- Coding benchmark — Kimi K2.7, GLM 5.2, MiniMax M3 (Akita): https://akitaonrails.com/en/2026/06/14/llm-benchmark-kimi-2-7-code-glm-5-2-minimax-m3-local/
- Open-model landscape June 2026 (WhatLLM): https://whatllm.org/best-open-source-llm
- Vercel Eve announcement: https://vercel.com/blog/introducing-eve
- Vercel Eve docs: https://vercel.com/docs/eve
- Eve overview (The New Stack): https://thenewstack.io/vercel-launches-eve-an-open-source-framework-that-treats-agents-as-directories/

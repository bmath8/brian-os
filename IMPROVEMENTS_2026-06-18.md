# Fleet Improvements — 2026-06-18 (deep-audit fixes)
_Branch: `deep-audit-fixes-2026-06-18`. Companion to `FLEET_DEEP_AUDIT_2026-06-18.md` (the findings) and `DEPLOY_NOTES_2026-06-18.md` (how to ship it). All work is in the repo only — NOT yet deployed to `~/.hermes/scripts` and NOT pushed. 28 tests pass in WSL._

## What changed and why (mapped to audit findings)

### New shared core — `runtime/fleet_common.py`
One module the whole fleet imports. Removes the copy-paste and wires the things that were "on paper":
- **Central config / paths** derived from `__file__` + env overrides (`FLEET_ROOT`, `FLEET_COMMS`, `HARMONY_DIR`, `OLLAMA_URL`, `FLEET_MODEL`, …). Moving the repo no longer breaks every script. → **A5**
- **`host_ip` / `read` / `read_harmony` / `strip_think`** — the functions that were duplicated in ~10 files now live once. → **A4**
- **`atomic_write` + `FileLock` + `state_update`** — `state.json` is now written to a temp file then `os.replace`d under a cross-process lock, with a re-read immediately before write. The read-modify-write race and the truncated-file-on-crash bug are gone. → **A1**
- **`model_for`** — resource-aware model gate (the old `safe_model` logic) now lives on the path agents actually call: `ollama_generate` runs every model choice through it, so any 14B request auto-downgrades to 8B under memory pressure. When 64 GB RAM lands, set `FLEET_MODEL=qwen3:14b` in **one** place. → **A2**
- **`ollama_generate`** — single resilient generate: shorter timeout (default 90 s), one retry, then a caller-supplied `fallback` instead of a hung cron; optional `fmt` for JSON-schema structured output. → **B3**, enables **B2**
- **`tracker_cell`** — header-aware Job_Tracker parser (finds the `Target`/`Actual` columns by **name**, survives column reordering, falls back to last-two-columns). Your #1-priority job numbers are no longer parsed by a fragile position heuristic. → **B2**
- **`log_run`** (uniform, with optional `ms`), **`age_needs`** (chronic "Needs you" items go weekly after 3 days — less brief fatigue → **C3**), **`already_ran_today`** (idempotency stamp → **B6**).

### Agents — all 9 refactored onto the core
Each now has a `main()` guard (so it's testable/importable) and uses the shared helpers:
- **`daily_brief.py`** — now **persists** the brief to `comms/daily_brief.md` + `comms/briefs/<date>.md` (a failed Telegram send no longer loses it, and the dashboard has a source). Uses `tracker_cell`, `age_needs`, fast-fail generate. → **C1, B2, B3, C3**
- **`overnight_worker.py`** — the self-verify critic is now a **different model** (`deepseek-r1:14b`, resource-gated), and **deterministic checks** run alongside the LLM judge: a draft that's too short or that claims to have sent/deployed/published is forced to `NEEDS_WORK` regardless of a sycophantic "APPROVED". → **B4**
- **`system_watchdog.py`** — same self-heal logic (PowerShell/gateway), now on atomic state writes + uniform logging.
- **`scout / learning / finance / health / weekly_review / model_review`** — DRY, atomic state, retry+fallback generate, uniform logging. Behavior preserved.

### Router + registry honesty
- Removed the dead **`gemma4:26b`** reference in `shared/router.py` (now prefers the strongest *installed* local model) and deleted the disabled `gemma4:26b` entry from `shared/models.json`. `complexity_to_model` now describes reality (8B today, 14B post-RAM via `FLEET_MODEL`). → **A3**

### Tests + CI (the biggest reliability win)
- **`tests/test_fleet_common.py`** — 17 tests: atomic+locked state under concurrency (proves the race is fixed), `model_for` pressure cases, `ollama_generate` retry/fallback/structured, `tracker_cell` incl. column-reorder, idempotency, logging.
- **`tests/test_agents_smoke.py`** — every agent + both ops tools run end-to-end against a **mock Ollama** and a temp Harmony/comms tree, asserting outputs and valid `state.json`.
- **`tests/eval_models.py`** — manual head-to-head model harness for the monthly review.
- **`.github/workflows/tests.yml`** — runs the suite on every push/PR. A bad commit can't reach deploy. → **B1**

### New observability
- **`runtime/log_analyzer.py`** — turns the write-only `run_log.md` into `comms/fleet_health.md`: per-agent runs/fail-rate/latency + flags for silent degradation (failures, or no run in >36 h). → **E1**
- **`runtime/build_dashboard.py`** — one self-contained `comms/dashboard.html` (no server): agent status cards, today's brief, fleet-health flags, system status, RAM. → **E2**

## Tier 2 — capability upgrades (also built + tested this session, 41 tests total)
- **Injection-hardening (F1)** — `fc.wrap_untrusted()` fences ingested content as DATA and neutralizes common hijack markers ("ignore previous instructions", role tags, etc.). Applied to the overnight worker's queue items and the learning agent's dropped notes.
- **Local RAG memory (D1)** — `fc.ollama_embed()` + `fc.cosine()` + `runtime/memory_index.py`: chunks Harmony + fleet docs + comms, embeds with `nomic-embed-text`, stores vectors in a plain JSON file, retrieves by pure-Python cosine. The brief now pulls the *relevant* chunks via `memory_index.context_for(...)` instead of the first 4000 chars — and falls back to truncation automatically until the embed model is pulled (zero behavior change before then). Build: `python3 runtime/memory_index.py`.
- **CoS cross-domain synthesis (C2)** — the brief now runs a structured-output (`fmt` JSON schema) synthesis pass over the day's signals and leads with **"🎯 Today's ONE thing"** + **"🔗 Connections"** (e.g. runway vs. application pace). Degrades silently if the model hiccups.
- **Real learning loop (D2) + approval feedback (D3)** — `runtime/srs.py` (Leitner spaced-repetition store) drives the learning agent: it surfaces cards that are **due**, generates new ones only when the pool runs low, and supports grading (`learning_agent.py --grade <id> 1|0`). `runtime/feedback.py` records approve/reject decisions (you move a review file into `review/approved` or `review/rejected`), and the overnight worker now **few-shots from `review/approved/`** so drafts drift toward your taste.

## Tier 2+ — two-way command grammar
- **`runtime/commands.py`** — `handle(text) -> reply` over the blackboard: `/help /status /queue <task> /approve <id> /reject <id> /grade <id> 1|0 /snooze <agent> <days>`. Pure, no network, **no second Telegram poller** (that would 409 against the gateway). Works from the CLI today; wires into the gateway's existing inbound handler with one line (call `commands.handle()` when a message starts with `/`). `/snooze` mutes an agent's "Needs you" items, and the brief now respects it (`fc.snooze` / `fc.snoozed_agents`).

## Still open / deliberately not done here
- **Deploy** to `~/.hermes/scripts` and **push** to GitHub — left for Brian (Yellow per GUARDRAILS). See `DEPLOY_NOTES_2026-06-18.md` (now includes `nomic-embed-text`, memory/feedback crons, and the Telegram command hook).
- **Gateway hook for the command grammar** — one line in the Hermes inbound handler; touches the live gateway so it's a do-together (Yellow).
- **64 GB RAM** + Stage-2 always-on box — hardware/income gated.

# Agent 03 — Overnight Worker
_The drafter. Runs while Brian sleeps; drains the queue and produces the drafts he approves next morning._

- **Owns:** turning queued tasks into drafts (proposals, tailor/prep, research digests, etc.).
- **Why it exists:** high-quality drafting is slow; do it offline at big-model quality, surface for approval. _Solves:_ daytime latency, inconsistent drafts.
- **Cadence:** daily, 2:00 AM (cron `overnight-worker`, `no_agent` script `overnight_worker.py`).
- **Tier/model:** escalates to **`qwen3:30b-a3b`** (MoE, 30B knowledge / ~3B active) gated on free VRAM via `fleet_common.model_for()`; **`deepseek-r1:14b`** as the self-critic; runs at 16k context.
- **Deliver:** writes draft files into `comms/review/` (pending approval); never sends.

## What it does (as implemented)
- Drains `comms/queue/*.md` (tasks other agents queued — e.g. gig-scanner proposal requests, research digests).
- Self-verify loop: drafts, then the critic checks it against guardrails; only surfaced drafts that pass.
- Deterministic guardrail checks (draft-only invariant, no untrusted-injection leaks).
- `gig_scanner` queues strong (score ≥4) matches here for proposal drafts.

## Output (writes)
- `comms/review/*.md` — pending Brian's `/approvedraft` / `/rejectdraft`.
- `state.json` slice `overnight`.

## Hard rule
Draft-only. Never sends, posts, deploys, or spends. Approvals happen in Telegram during the day.

## Done-when
Queue empty or drained to review; every draft passes the critic; pending items visible in the brief's "Needs you."

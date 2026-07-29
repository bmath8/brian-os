# Agent 10 — Career
_The job-hunt command center. Apps-vs-target, streak, follow-ups, interviews._

- **Owns:** the job hunt scoreboard — the **first thing in the brief** (apps-vs-target).
- **Why it exists:** the #1 goal is landing a dev job; this keeps that front-and-center with real numbers. _Solves:_ lost momentum, forgotten follow-ups.
- **Cadence:** daily, 6:53 AM (cron `career`, `no_agent` script `career_agent.py`).
- **Tier/model:** free local `qwen3:8b`; deterministic parse of `03_Career/Job_Tracker.md` + one light LLM nudge.
- **Deliver:** writes `comms/career.md` + `comms/networking.md` + `state.json` slice.

## What it does (as implemented)
- Apps-vs-target scoreboard (weekly/monthly goal vs logged applications).
- Streak tracking, follow-ups due (deterministic date math), stale apps, upcoming interviews.
- Auto-drafts follow-up messages → `comms/review/` (draft-only; Brian approves).
- Feeds `outcome_learner` (which apps actually got responses).

## Output (writes)
- `comms/career.md` — the scoreboard source (leads the brief).
- `comms/networking.md` — networking nudges.
- `state.json` slice `career` (summary consumed by `ceo_report`).

## Hard rule
Draft-only for any outbound message. Never sends applications or emails itself.

## Done-when
Scoreboard leads the brief; follow-ups due are listed; auto-drafts in the review queue, not sent.

# Loop & Skills Doctrine — how we build agents from here on
_Cross-project standard. Synthesized from two June 2026 pieces: Van Horn "WTF Is a Loop?" and KingWilliam "23 Skills". Apply to every Brian OS project. Last updated 2026-06-17._

## The thesis (one line)
**Stop being the thing inside the loop.** Write a loop that prompts the agent, reads the result, decides if it's done, and repeats — and make the reusable unit a **skill**, not a one-off prompt.

## What a loop actually is
> A loop is **cron + a decision-maker in the body**: the model (not a hardcoded branch) picks the next action each tick, checks its own work, and decides whether to continue.

Lineage to know: ReAct (2022) → AutoGPT (2023) → ralph loop (2025) → `/goal` (2026) → **multi-agent orchestration loops (now)**. Single-agent ralph is old hat; loops supervising other loops, on a schedule, with durable git-backed state, is the new layer.

## The 5 non-negotiables for any loop we build
1. **A decision-maker in the body** — the agent decides the next step; we don't hardcode the steps.
2. **Self-verification** — the loop must check its own work end-to-end. "A loop is only as good as its feedback." An open loop with no verification is a machine for confident mistakes.
3. **Hard stops** (the part that keeps the bill sane — the loop, not the model, is now the expensive part):
   - max iteration count
   - no-progress detection (stop if it stops improving)
   - token/dollar/time budget ceiling
4. **Durable state** — git-backed or file-backed so it survives a crash/restart (don't assume the terminal stays open).
5. **Scheduled, not babysat** — runs on infrastructure time (cron), not your attention.

## Skills are the compounding asset
A **skill** = a folder with a `SKILL.md`: a header (`name` + `description` = *when to use it*) and a body (the instructions). The agent auto-loads it when a request matches — you write the recipe once, it fires forever.
- **Prompt = teach the agent the job once. Skill = teach it the job forever.**
- A loop that calls sharp, named, tested skills **compounds**. A loop that re-derives everything just burns money.
- Locations: personal `~/.claude/skills/`, project `.claude/skills/`. Hermes uses the same agentskills.io standard (`hermes skills`).

## How our fleet already matches this (and where it falls short)
| Doctrine | Fleet today | Gap to close |
|---|---|---|
| cron + decision-maker | 5 scheduled agents ✅ | overnight-worker is single-pass (drafts once) — make it a real decide→verify→iterate loop |
| self-verification | partial (watchdog self-heals) | add a verify step: worker reviews its own draft before writing to review/ |
| hard stops | `MAX_PER_RUN`=5 ✅ | add no-progress detection + a token/time budget per loop |
| durable state | git + `comms/` blackboard ✅ | keep |
| skills | ad-hoc `runtime/` scripts | **build a real skills library** (SKILL.md) the agents call |

## Action items (apply across projects)
1. **Build a skills library** under `~/.claude/skills/` + Hermes. First skills to build (from the 23, tuned to Brian): `second-brain` (we already do MEMORY.md ✅), `plan-first` (no code before a plan), `voice-match` (Brian's writing voice), `deploy-runbook`, `weekly-review`, `idea-killer`, `agentic-reviewer`, `bug-hunter`. Build 3 this week; start with **plan-first** + **voice-match**.
2. **Upgrade the overnight worker into a true loop:** draft → self-verify against the task → revise (cap 3 iterations, no-progress stop) → write to review only when it passes its own check.
3. **Add loop hard-stops to GUARDRAILS:** every autonomous loop declares max-iterations, no-progress rule, and a budget ceiling.
4. **Every repeated task becomes a skill** (Steinberger's rule: do it twice → make it a skill; do something hard → make it a skill afterward).

## Visual planning skills — use SELECTIVELY (token-aware)
Steve / Builder.io (@Steve8708) open-sourced `/visual-plan` (plans as rich MDX: diagrams, interactive API specs, schema changes, annotated code, zoomable wireframes) and `/visual-recap` (same visual treatment for reviewing an agent's work / a PR). Thesis: "plans are the new intermediate representation" — review a wireframe before the agent codes.

**Decision (cost/benefit): adopt ONLY for UI/frontend work.** It is genuinely better when there's a UI to see — but it costs **materially more tokens** than a plain-text plan (it generates MDX + components + diagrams).
- ✅ Use on: portfolio, Boombox frontend, AI Job Hunter UI, any wireframe-able task.
- ❌ Don't use on: the fleet, scripts, infra, backend, docs — there the lean `plan-first` (plain markdown) is correct and cheaper.
- **Install lazily:** clone Steve8708's open-source skills into `~/.claude/skills/` only when we next start a UI task — not preemptively.
- Token rule of thumb: default to the cheapest plan format that conveys the intent; reach for visual only when a picture genuinely saves back-and-forth.

## The mindset
You write the **intent and the stopping behavior**; the loop prompts the agent each tick; the model is a subroutine; skills are the library it calls. Your job moves up an altitude: decide *what* to build and *when to stop*, not type every step.

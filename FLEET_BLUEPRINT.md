# Brian OS — Agent Fleet Blueprint
_The architecture for a fleet of agents that work for Brian continuously. Last updated 2026-07-15 (reconciled: 25 cron jobs live)._

> ⚠ **Runtime since changed:** the blackboard/agent design below is current, but the host is now **native Windows Hermes** (not WSL), with **25 cron agents** + a two-way command plugin + 8 skills. Per-agent specs live in `agents/` (`01_*`–`24_*`); see **[README.md](README.md)** and **[CURRENT_STATE.md](CURRENT_STATE.md)**.

> This blueprint was the plan; it's now **built**. See §3 for the agents as actually shipped, `CURRENT_STATE.md` for live status, and `ROADMAP.md` for what's done vs next.

## 1. The mandate
Build a fleet of agents — each owning one goal — that run on a cadence, talk to each other through a shared layer, anticipate needs, and head off problems before they hit. Cost-effective now (RTX 4070 + cheap models), scaling as income grows. Built so Brian **learns and retains** as it runs, never bypassed.

**Design contract (inherited from [Harmony_Charter](../../../Users/mathe/OneDrive/Desktop/Harmony/Harmony_Charter.md)):** reject complexity > value; everything states Why/How-often/What-problem; recover, don't require perfection.

## 2. Operating decisions (locked 2026-06-16)
| Decision | Choice | Implication |
|---|---|---|
| Home | Dedicated project `C:\Brian\02_Projects\brian-os-fleet` + GitHub | Off OneDrive (code rule). Harmony only links here. |
| Model routing | **Hybrid balanced** | Local Ollama for bulk/cheap; cloud frontier for user-facing or hard tasks. See [shared/ROUTING.md](shared/ROUTING.md). |
| Autonomy | **Autonomous within guardrails** | Agents act inside set limits, report after. Hard stops in [GUARDRAILS.md](GUARDRAILS.md). |
| Trigger | Scheduled tasks (cadence) + on-demand | "Always working" = each agent wakes on its schedule, does its job, writes results. |

## 3. The fleet (goals → agents)
Each of Brian's goals maps to one agent. One agent = one job, one owner, one output file.

**As shipped — 25 cron agents** (the original 10 below + 15 added since; full list in `agents/README.md`):

| Agent | Owns | Cadence | Primary output |
|---|---|---|---|
| **Chief of Staff** | Orchestration / daily focus | Daily 7am | `comms/daily_brief.md` → Telegram (job-hunt #s, needs, review, Money&Health, System/RAM, Recall) |
| **System Watchdog** | Infra health + self-heal | Every 4h | `comms/system_status.md` (disk/RAM/Ollama/gateway/backup; self-heals; alert-on-change) |
| **Overnight Worker** | Draft queued tasks safely | Daily 2am | `comms/review/*.md` (draft→self-verify→revise; never sends) |
| **Learning** | Retain knowledge | Daily 6:45am | `comms/recall.md` (3 active-recall questions) |
| **Finance** | Runway + credit | Daily 6:50am | `comms/finance.md` (never invents numbers) |
| **Health** | Body composition | Daily 6:52am | `comms/health.md` (never invents data) |
| **Weekly Review** | Weekly funnel/reflection | Sun 5pm | Harmony `02_Weekly_Reviews/` + Telegram |
| **Harmony Backup** | Off-OneDrive insurance | Daily 1:30am | mirror → `C:\Brian\Harmony_backup` |
| **Model Review** | Keep models current | Monthly | `comms/model_review.md` + checklist |
| **Scout** | Free job/opportunity discovery | Daily 6:40am | `comms/scout.md` (DuckDuckGo, no key, no cost) |

_Future (not built): **Job Hunter** (fleet-side sourcing — AI Job Hunter app already covers tailoring), draft-only per Guardrails when built. Non-scheduled ops helpers added 2026-06-18: `log_analyzer.py` (fleet health) + `build_dashboard.py` (HTML dashboard)._

Chief of Staff is the **hub**: it reads every producer's output + `state.json` and assembles the one brief Brian reads each morning. It was built first as the template every other agent copies (input → local model → write to `comms/`).

## 4. How agents communicate (the comms layer)
Agents don't call each other live. They communicate through **shared files** — simple, debuggable, tool-agnostic, survives any agent crashing.

```
comms/                 (runtime files gitignored; regenerated each run)
  daily_brief.md       ← Chief of Staff writes (the human-facing summary)
  system_status.md     ← Watchdog writes, Chief reads
  finance.md           ← Finance writes, Chief reads
  health.md            ← Health writes, Chief reads
  recall.md            ← Learning writes, Chief reads
  resource_status.json ← host RAM/commit/VRAM (probe), read by Watchdog + brief
  review/*.md          ← Overnight Worker drafts, surfaced by Chief
  state.json           ← shared state: per-agent {last_run, status, summary, needs_human[]}
```

**Protocol:** each agent (1) reads its inputs (its own last state + any upstream files), (2) does its work, (3) writes its output file + updates its slice of `state.json` with `{last_run, status, summary, needs_human[]}`. The Chief reads all `needs_human[]` items and escalates them in the brief. This is the "blackboard" pattern — robust and the cheapest thing that works (Charter principle 10).

## 5. Model routing (hybrid) — summary
Full table in [shared/ROUTING.md](shared/ROUTING.md). Default ladder:
1. **Local (free)** — Ollama `qwen3-coder`/`llama` on the 4070 for parsing, drafting, classification, summarizing.
2. **Cheap cloud** — Haiku / GPT-5-mini / Gemini Flash for anything user-facing but routine.
3. **Frontier** — Sonnet/Opus/GPT-Codex for hard reasoning, final application drafts, architecture.
Rule: start one tier down from where you think you need; escalate only on failure. Logs in `logs/` track spend so we know when to upgrade.

## 6. Learning & retention loop (non-negotiable)
The fleet must make Brian *smarter*, not just busier. Every agent that produces knowledge feeds the Learning agent, which:
- writes a plain-language note (what/why/how) to `learning_log.md`,
- generates 2–3 spaced-repetition questions per concept,
- surfaces 3 questions in each morning brief (active recall before new input).
This satisfies "find my own effective way to learn and actually retain." Retention is a first-class output, not a side effect.

## 7. Anticipation (see problems before they happen)
Guardrails + the Scout agent + `state.json` flags. Examples the fleet should pre-empt:
- OneDrive churn → Chief checks sync health, warns before a wipe (the two past incidents).
- Job-search stall → Job Hunter flags if apps/week drops below target.
- Runway → Finance flags when projected runway < 60 days.
- Stale knowledge → Learning flags concepts not reviewed in 30 days.

## 8. Scaling path (cheap now → upgrade as income grows)
| Stage | Trigger | Upgrade |
|---|---|---|
| **Now** | $0 budget | Local Ollama + scheduled tasks + free tiers. Hybrid only for final outputs. |
| **First income** | Job landed | Paid API budget for daily frontier calls; add Scout agent. |
| **Stable income** | 3+ months | Dedicated always-on runner (mini-PC or cloud VM) so agents run independent of the laptop; more VRAM for bigger local models. |
| **Scale** | Multiple income streams | Orchestrator service, web dashboard over `comms/`, more specialized agents. |

## 9. Build order
See [ROADMAP.md](ROADMAP.md). Short version: **Chief of Staff (now) → Job Hunter → Learning → Finance → Health → Scout.** Each new agent copies agent #1's shape: a spec in `agents/`, a prompt in `prompts/`, a `comms/` output, a schedule.

## 10. Open questions for Brian (refine as we go)
- Preferred morning brief time? (defaulting to 7:00 AM)
- Which connectors to wire first — Gmail, Calendar, a job board? (each unlocks an agent)
- Comfort level letting the Job Hunter *submit* applications vs. only draft them? (currently: draft only — see GUARDRAILS)

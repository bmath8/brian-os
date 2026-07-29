# Agent specs — read this first (reconciliation note, 2026-07-15)

⚠️ **These `01_*`–`24_*` spec files describe every live cron job in the fleet.** As of 2026-07-15 the live fleet runs **25 cron jobs** (all `last_status: ok`). `CURRENT_STATE.md` is still the authoritative runtime snapshot, but the per-agent specs below are now kept in sync with it. When they disagree, `CURRENT_STATE.md` wins.

## Live cron agents (authoritative — 25 jobs, from `cronjob list` 2026-07-15)
| # | Cron name | Script | Schedule | Role |
|---|---|---|---|---|
| 01 | daily-brief | daily_brief.py | 7:00 daily | Chief of Staff — morning brief aggregator |
| 02 | system-watchdog | system_watchdog.py | /4h | System health + self-heal (`hermes doctor`) |
| 03 | overnight-worker | overnight_worker.py | 2:00 daily | Queue drafter (self-verify loop) |
| 04 | learning-agent | learning_agent.py | 6:45 daily | SRS recall builder |
| 05 | finance | finance_agent.py | 6:50 daily | Runway + credit (Harmony) |
| 06 | health | health_agent.py | 6:52 daily | Body-comp consistency (Harmony) |
| 07 | weekly-review | weekly_review.py | Sun 17:00 | Sunday funnel + reflection |
| 08 | scout | scout_agent.py | 6:40 daily | Free job/opportunity discovery |
| 09 | calendar | calendar_agent.py | 6:55 daily | Google Calendar → today's events |
| 10 | career | career_agent.py | 6:53 daily | Apps-vs-target, streak, follow-ups |
| 11 | inbox | inbox_agent.py | 6:48 daily | Surfaces new Harmony/00_Inbox files |
| 12 | dashboard | build_dashboard.py | :05 hourly | Live HTML dashboard |
| 13 | currency | currency_agent.py | 6:58 Mon-Sat | Dep/security currency sweep |
| 13b | currency-weekly | currency_weekly.py | Sun 16:30 | Weekly deep-dive + safe upgrade PRs |
| 14 | research | research_agent.py | Sun 18:00 | Deep research digests |
| 15 | wiki | wiki_agent.py | Sun 16:45 | Wiki/knowledge upkeep |
| 16 | outcome-learner | outcome_learner.py | Sun 16:50 | Outcome → lesson extraction |
| 17 | gig-scanner | gig_scanner.py | 7:10 Mon-Sat | Gig/contract leads |
| 18 | ceo-report | ceo_report.py | 7:30 1st | Monthly CEO report |
| 19 | fleet-health | log_analyzer.py | 6:59 daily | Fleet health from logs |
| 20 | skill-miner | skill_miner.py | Sun 18:30 | Mines sessions → skill DRAFTS |
| 21 | harmony-backup | backup_harmony.py | 1:30 daily | Harmony mirror backup |
| 22 | model-review | model_review.py | 1st 3:00 | Monthly model + security review |
| 23 | memory-index | memory_index.py | 1:20 daily | Rebuild memory/RAG index |
| 24 | feedback | feedback.py | Sun 17:00 | Weekly feedback → backlog |

## What's stable across all of them
- **Host:** native Windows Hermes (no WSL). Ollama `localhost:11434`.
- **Models:** default `qwen3:8b`; BIG=`qwen3:30b-a3b` (VRAM-gated via `fleet_common.model_for()`); code=`qwen3-coder:30b`; vision=`gemma3:12b`; critic=`deepseek-r1:14b`. (The old `safe_model.py` RAM-gate was **retired** 2026-07-15 — dead + WSL-path bug.)
- **Coordination:** blackboard `comms/*.md` + atomic `state.json`; brief aggregates every producer's `needs_human[]`.
- **Autonomy:** all `no_agent` scripts — deterministic + cheap. Agents draft; nothing sends/spends/deploys without approval.

## Per-file status (all current as of 2026-07-15)
Every spec `01_*`–`24_*` maps 1:1 to a live cron job above. Nothing stale.

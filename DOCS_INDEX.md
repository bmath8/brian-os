# 📂 Docs Index — START HERE
_The single entry point for this repo's docs. Updated 2026-07-15. If you read one file first, read `CURRENT_STATE.md`._

There are two kinds of docs here: **🟢 living** (kept current — trust them) and **📚 dated history** (point-in-time journal — context, not current truth). When they disagree, the living doc wins.

## 🟢 Living — read these (current truth)
| Doc | What it's for |
|---|---|
| **`CURRENT_STATE.md`** | **Authoritative handoff.** Read first in any new session. What's running, how it's wired, what's left. |
| `MASTER_STATUS.md` | High-level status dashboard of the fleet. |
| `NORTH_STAR.md` | The why — goals the fleet serves. |
| `ROADMAP.md` | Where it's going next. |
| `GUARDRAILS.md` | Hard rules every agent/loop must obey (approval gates, budgets, logging). |
| `FLEET_BLUEPRINT.md` | Architecture — agents, blackboard `comms/`, how coordination works. |
| `FLEET_GAPS.md` | Living register of open holes → fixes → status. |
| `LOOP_AND_SKILLS_DOCTRINE.md` | Cross-project standard for building loops & skills. |
| `MODEL_REVIEW_PROCESS.md` | How/when models get re-evaluated. |
| **`MASTER_AUDIT_AND_IMPROVEMENTS_2026-06-20.md`** | **Current** whole-system audit + prioritized backlog + what was executed (incl. the GPU/VRAM optimization & the RAM-myth correction). |

## 📚 Dated history — context, not current truth (safe to skim/ignore)
These are the journal. Keep for provenance; don't treat as current.
| Doc | Snapshot of |
|---|---|
| `AUDIT_2026-06-17.md` | First structured audit. Superseded by the deep audit. |
| `FLEET_DEEP_AUDIT_2026-06-18.md` | Deep audit (the big one). |
| `IMPROVEMENTS_2026-06-18.md` | Improvements applied that day. |
| `IMPROVEMENTS_AND_OPTIMIZATIONS_2026-06-20.md` | Backlog as of today — now rolled into `MASTER_AUDIT...`. |
| `DEPLOY_NOTES_2026-06-18.md` | Native-Windows deploy notes. |
| `MODELS_AND_TOOLS_REVIEW_2026-06-17.md` | Model/tool review snapshot. |
| `PDF_RESEARCH_APPLIED_2026-06-19.md` | What the IAM/Autonomous-Intern PDF research changed. |
| `SKILLS_RECOMMENDATIONS_2026-06-19.md` | Skill build recommendations. |
| `TIPS_AND_OPTIMIZATIONS.md` | Running tips collection. |
| `_archive/` | Fully retired docs (EVE eval, systemd steps, old runtime/VM setup). |

## Convention going forward
- **Living docs** stay at root and get edited in place.
- **Point-in-time docs** are dated `NAME_YYYY-MM-DD.md` and become history the moment they're written — fold their durable conclusions into a living doc, then leave the dated one as journal.
- One source of truth per fact. If you update a fact, update the living doc, not a new dated file.

- [MODERNIZATION_PROCESS.md](MODERNIZATION_PROCESS.md) - the Modernization & Currency system (currency_agent.py): keeps deps/code/docs/security/tooling current; daily flags + weekly deep-dive + safe auto-upgrade PRs. Sibling of MODEL_REVIEW_PROCESS.md.

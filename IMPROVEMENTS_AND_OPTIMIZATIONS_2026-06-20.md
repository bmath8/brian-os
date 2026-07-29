# Improvements & Optimizations — remaining backlog
_What's still worth doing, prioritized by value ÷ effort. 2026-06-20. The system is now mature (native Windows, tested, RAG, skills, calendar live), so these are enhancements, not fixes._

## Tier 1 — Reliability (low effort, do soon)
1. **External dead-man's-switch.** Today nothing tells you if the whole fleet silently dies (the watchdog lives *inside* the fleet). Add a free [healthchecks.io](https://healthchecks.io) ping at the end of the morning brief — if the brief doesn't run, healthchecks emails/texts you. This is the one monitoring gap a self-hosted system can't cover itself. **~30 min.**
2. **Log rotation.** `logs/run_log.md` grows forever (every agent appends); Hermes `agent.log`/`errors.log` too. Add a tiny rotation (keep last N days / cap size). Prevents slow bloat. **~20 min.**
3. **Official gateway auto-start as a belt.** The gateway runs "manually" (revived by the Startup keepalive). Also register `hermes gateway install` (Scheduled Task, ONLOGON) so there are two independent auto-start paths. **~15 min, do-together (it blocks the shell).**
4. **Back up the un-backed-up bits.** `.env` (secrets) and Hermes `state.db` (sessions) aren't in git (correctly) and aren't backed up either. Add an encrypted local copy to `C:\Brian\Harmony_backup` so a disk failure doesn't lose the tokens/sessions. **~20 min.**

## Tier 2 — Intelligence (biggest quality wins available without new hardware)
5. **Escalate high-stakes drafts to a stronger model.** You're now logged into **Nous Portal**, but everything still runs on local `qwen3:8b`. Keep the cron fleet local (free), but let the **chat agent + the job-application/outreach skills escalate to a stronger model** for the things that matter most (your actual job applications). This is the single biggest quality lever that needs no hardware. **~1 hr** (wire model selection per-skill; cost stays near-zero since escalation is occasional).
6. **RAG reranking + show sources.** The memory retrieves by cosine similarity; a light rerank (2026 best practice) sharpens results, and surfacing *which* note an answer came from builds trust. **~1 hr.**
7. **Tighten the spaced-repetition loop.** The brief lists due cards but grading needs you to type a command. Make the brief ask **one** due card and accept your Telegram reply as the grade — turns passive recall into a real habit. **~45 min.**

## Tier 3 — Capability
8. **Gmail + Todoist into the brief** *(deferred to 2026-06-21 at your request).* Gmail = unread count + important senders; Todoist = today's tasks. Same private-feed/API pattern as the calendar.
9. **`voice-match` real samples** *(waiting on you)* — 3–5 things you've written; makes every draft sound like you.
10. **Two more chat skills:** `finance-check` (on-demand runway/cut analysis), `daily-plan` (time-block the brief + calendar). **~30 min each.**
11. **Live dashboard.** `build_dashboard.py` makes a static HTML; turn it into a glance-able page you can keep open (or a Cowork artifact that refreshes). **~1 hr.**

## Tier 4 — OpenClaw: looked into it (verdict: don't switch, borrow one idea)
**What it is:** [OpenClaw](https://www.digitalocean.com/resources/articles/what-is-openclaw) — a viral (~68k★) open-source personal AI agent by Peter Steinberger (PSPDFKit). Node.js, bring-your-own-key (incl. local models), **memory stored as Markdown files**, and an April-2026 **TaskFlow** orchestration layer.

**vs your Hermes setup:**
| | Hermes (you) | OpenClaw |
|---|---|---|
| Language | Python | Node.js |
| Memory | vector (ChromaDB) + skill auto-generation + your nomic-embed RAG | Markdown files + provenance labels |
| Channels | Telegram/Discord/Slack/15+ gateway | mostly chat |
| Native Windows | ✓ (you rely on this) | weaker |
| Scale | #1 on OpenRouter (~224B tok/day) | ~186B tok/day |

**Verdict: do NOT migrate.** Your entire system — native-Windows host, 13 cron agents, the plugin, 9 skills, RAG, Telegram — is built on Hermes and working. Switching to OpenClaw means rebuilding all of it for no functional gain, and it fails your own tool-adoption filter ("don't replace something already working free"). OpenClaw is excellent, but it's a *lateral* move.

**Worth borrowing (1 idea):** OpenClaw's **TaskFlow** = multi-step task orchestration. Your overnight worker is single-pass (draft → self-verify → revise). A TaskFlow-style planner would let it take a bigger job ("research X, then draft a plan, then a checklist"), break it into steps, and work each — a real upgrade to the overnight worker when you want it. (Memory-provenance, OpenClaw's other headline, you already have — your RAG stores each chunk's `source`.)

## Tier 5 — Hygiene
12. **Delete or wire `shared/router.py`.** It's dead code (no agent calls it). Either wire it as the escalation path for Tier-2 #5, or remove it. **~15 min.**
13. **Refresh `agents/01–08` specs** — written for the WSL/10-agent era; minor drift. **~30 min.**
14. **Consider a secrets manager** (Hermes supports Bitwarden Secrets via `hermes secrets`) instead of plaintext `.env`. Low priority for a personal box. 

## Gated on hardware / income (the real ceiling)
- **64 GB RAM** → flip `FLEET_MODEL=qwen3:14b` (one line). The #1 quality lever; host is currently RAM-bound. **Prime Day.**
- **$150–250 used mini-PC** (Linux) as a dedicated always-on box — removes the last single-machine risk. **When income allows.**

## Suggested order
This week (free, high-value): **#1 dead-man's-switch → #5 escalate job-application drafts → #7 tighten recall → #8 Gmail/Todoist → #9 voice-match.** Everything else is polish or gated.

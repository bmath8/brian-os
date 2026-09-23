# Brian OS — Agent Fleet

A personal **always-on AI assistant fleet** that runs on Brian's own PC: a set of scheduled
agents that prepare a morning brief, watch the system, draft work overnight, and track the
job hunt, plus a **two-way Telegram assistant** with an on-demand skill library — all on a
**local LLM** (free, private). Built on **Hermes Agent v0.17.0, native Windows** (no WSL).

> **Status (2026-09-23):** the live fleet is operational on native Windows — 30 agents registered and active, 226 tests passing (verified 2026-09-23 in the private working repo). **This public mirror is a 2026-07-29 snapshot:** 25 agent specs and 81 tests (80 pass, 1 skipped on Linux CI).

## What it does
- **Morning brief → Telegram (7:00).** Leads with the day's ONE thing + cross-domain connections
  (job funnel vs. runway vs. health), job-hunt numbers, overnight drafts to review, fresh job
  listings, system status, and spaced-repetition recall questions.
- **30 scheduled agents** (all local, free): chief-of-staff (brief), system-watchdog (/4h, self-heal
  + `hermes doctor`), overnight-worker (drafts queued tasks, self-verifies), scout (free job
  discovery), learning (spaced repetition), finance + health (tracker nudges, never invents data),
  calendar (Google Calendar → today's events), weekly-review, harmony-backup, model-review,
  memory-index, feedback.
- **Two-way Telegram control:** `/fleet` (status), `/addtask <task>`, `/approvedraft <id>`,
  `/rejectdraft <id>`, `/grade <id> 1|0`, `/snooze <agent> <days>`, `/research [text/url]`,
  `/watchlist [@handle]`.
- **Chat-agent skills** (load on matching request): job-application, outreach, interview-prep,
  application-follow-up, project-showcase, build-in-public, learn-and-retain, weekly-reflection,
  voice-match (drafts in Brian's voice).
- **Local RAG memory** over Harmony + the fleet (nomic-embed), a **spaced-repetition learning
  loop**, and an **approval-feedback loop** (the overnight worker learns from drafts you approve).

## Architecture (native Windows)
```
Telegram  <->  Hermes gateway (native, %LOCALAPPDATA%\hermes)  <->  local Ollama (qwen3:8b, localhost:11434)
                     |  in-process cron scheduler (30 jobs)
                     |  fleet-commands plugin (/fleet ...) + 9 skills
                     v
        comms/ blackboard (state.json, briefs, review/, .memory/, .srs)  <-  C:\Brian\02_Projects\brian-os-fleet
```
- **Model:** local `qwen3:8b` is the default (provider `custom`, `localhost:11434/v1`). **Nous Portal**
  is logged in and available as an *escalation* only — local stays default ($0, private).
- **Coordination:** blackboard pattern — agents read/write `comms/*.md` + `state.json`; the brief
  aggregates. No agent calls another directly.
- **Resilience:** the gateway runs detached (`pythonw`); a Startup **keepalive** (every 3 min)
  ensures Ollama + the gateway are up and revives them after a crash/sleep/logon.

## Repo layout
| Path | What |
|---|---|
| `runtime/*.py` | the agents + shared core (`fleet_common.py`, OS-aware) → deployed to `%LOCALAPPDATA%\hermes\scripts` |
| `runtime/plugins/fleet-commands/` | the Telegram slash-command plugin |
| `runtime/skills/` | the chat-agent SKILL.md library |
| `tests/` | 81 unit + smoke tests in this mirror (pytest); CI in `.github/workflows/tests.yml` |
| `shared/` | model registry + routing policy (reference) |
| `comms/` | runtime blackboard (gitignored runtime data) |
| `runtime/_wsl_legacy/`, `_archive/` | historical WSL-era scripts/docs (not used) |

## Operate it
- **Deploy code:** edit `runtime/`, then `Copy-Item runtime\*.py %LOCALAPPDATA%\hermes\scripts`. Commit/push via **Windows git**.
- **Gateway:** `hermes gateway status` / `stop`. To (re)start, launch detached:
  `Start-Process pythonw -ArgumentList '-m','hermes_cli.main','gateway','run' -WindowStyle Hidden`
  (`hermes gateway start`/`install` block the shell — don't use them headless).
- **Tests:** `python -m unittest discover -s tests` (passes on native Windows and WSL).
- **Diagnostics:** `hermes doctor`.

## Guardrails (don't break)
Agents **draft only** — never send/spend/deploy/delete without approval. Code lives in
`C:\Brian` + GitHub, never OneDrive. Ingested content is treated as data, never instructions.
Don't blind-`hermes update` (test on a copy). See [GUARDRAILS.md](GUARDRAILS.md).

## Key docs
[FLEET_BLUEPRINT.md](FLEET_BLUEPRINT.md) (start here) · [MASTER_STATUS.md](MASTER_STATUS.md) ·
[GUARDRAILS.md](GUARDRAILS.md) · [LOOP_AND_SKILLS_DOCTRINE.md](LOOP_AND_SKILLS_DOCTRINE.md) ·
[PDF_RESEARCH_APPLIED_2026-06-19.md](PDF_RESEARCH_APPLIED_2026-06-19.md) ·
[SKILLS_RECOMMENDATIONS_2026-06-19.md](SKILLS_RECOMMENDATIONS_2026-06-19.md)

---

_This is a public showcase mirror of a private repository. It contains the full source and
test suite; day-to-day operational notes and machine state are kept in the private original._

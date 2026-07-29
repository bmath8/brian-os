# Skills to Add Across Projects — recommendations
_What would make each project easier/more efficient. 2026-06-19._

There are **three skill surfaces** in your world; don't confuse them:
1. **Cowork/Claude skills** — fire when you work *with me* in the Cowork app. You already have a rich set installed; mostly a matter of *using* them.
2. **Hermes skills** (`SKILL.md` in `%LOCALAPPDATA%\hermes\skills`) — fire for your **two-way Telegram agent**. We just built 8.
3. **Dev/agent skills** (`.claude/skills/` in a code repo) — fire when an AI codes *on* that project.

## A. You already have these (Cowork) — just use them
| When you're doing... | Skill you already have | Project it helps |
|---|---|---|
| Specs / PRDs / feature planning | `product-management:write-spec`, `feature-spec` | AI Job Hunter |
| Code review before shipping | `engineering:code-review`, `review` | AI Job Hunter, fleet |
| Test strategy / writing tests | `engineering:testing-strategy` | AI Job Hunter, fleet |
| Debugging a nasty bug | `engineering:debug` | all code projects |
| Deploy checklist | `engineering:deploy-checklist` | AI Job Hunter, portfolio |
| Polished frontend/UI | `frontend-design`, `theme-factory`, `design:design-system` | Portfolio, AI Job Hunter UI, Boombox |
| Posters / visual art | `canvas-design`, `algorithmic-art` | Portfolio, Boombox cover art |
| Word/PDF/Excel/Slides output | `docx`, `pdf`, `xlsx`, `pptx` | résumé, reports, pitch decks |
| Data analysis / dashboards | `data:analyze`, `data:build-dashboard` | AI Job Hunter analytics |
| Brand consistency | `brand-guidelines` | Portfolio, all public assets |

**Action:** none to install — just invoke them by task. Biggest immediate wins: `frontend-design` + `theme-factory` on the **portfolio** (your shop window for jobs), and `product-management:write-spec` before any new AI Job Hunter feature.

## B. Worth ADDING — custom dev skills (highest leverage, from your own LOOP_AND_SKILLS doctrine)
These live in each repo's `.claude/skills/` and make any AI that codes on the project sharper. Your doctrine already named them; here's the priority order:

1. **`voice-match`** ⭐ — captures *your* writing voice from a few samples. This is the #1 multiplier: it improves the Hermes job-application/outreach/build-in-public skills AND any content the fleet drafts. **Needs from you: 3-5 things you've written** (a good message, a bio, a post). Then every drafted word sounds like you.
2. **`plan-first`** — forces a short written plan before any code change. Prevents the "agent rewrites half the file" problem on AI Job Hunter.
3. **`deploy-runbook`** — the exact deploy steps per project (you have this for the fleet; AI Job Hunter + portfolio need their own). Turns "how do I ship this again?" into one command.
4. **`bug-hunter`** — a repeatable reproduce→isolate→fix loop for AI Job Hunter.
5. **`agentic-reviewer`** — a self-review pass before any PR/commit (you proved the pattern in the overnight worker).

**Recommendation: build `voice-match` first** (it pays off across the fleet skills + your job hunt), then `plan-first` + `deploy-runbook` for AI Job Hunter.

## C. Worth ADDING — a few more Hermes skills (two-way agent), only the high-value ones
- **`finance-check`** — "where's my runway / what should I cut" on demand from your finance tracker (deeper than the daily nudge).
- **`daily-plan`** — "plan my day" that turns the brief + calendar into a time-blocked plan (great once we wire your calendar — see backlog).
- **`email-triage`** — only if/when we connect email; summarizes + drafts replies.

Skip finance/health-logging-heavy skills for now — the cron agents already cover the passive nudges; add the *interactive* ones above only if you'll use them.

## Bottom line / priorities
1. **Use** `frontend-design`/`theme-factory` on the portfolio and `write-spec` on AI Job Hunter (already installed).
2. **Build `voice-match`** (needs your writing samples) — biggest cross-project multiplier.
3. **Build `plan-first` + `deploy-runbook`** for AI Job Hunter.
Everything else is optional polish.

# Modernization & Currency Process — keep everything current
_Serves Brian's standing goal: "make sure we're never leaving lingering inefficiencies, old frameworks, outdated knowledge, stale docs — there are new features from every AI company and big project every day, include them all."_

This is the sibling of `MODEL_REVIEW_PROCESS.md`. That one keeps the **local models** current; this one keeps **dependencies, code, docs, security, and tooling** current — across the fleet, the employer-facing projects, and every other repo.

## The tool
`runtime/currency_agent.py`, driven by `shared/currency_watch.json`. Stdlib only (+ `gh`/`npm`/`pip`/`git` via subprocess); every external call is guarded so a failure flags "unknown" and never crashes the cron.

Two cadences (Brian's choice: **daily flags + weekly deep-dive**):
```
python currency_agent.py            # DAILY  — open security alerts + new releases of watched tools (cheap, ~20s)
python currency_agent.py --weekly   # WEEKLY — + outdated deps, stale projects, SAFE auto-upgrades (tested), AI-ecosystem digest
python currency_agent.py --weekly --print   # same, but echo the full report to stdout (manual runs)
```

### What it checks
- **Security:** open Dependabot alerts per GitHub repo → **urgent daily flag** (direct Telegram) if any high/critical.
- **Releases:** latest tag of each repo in `releases_watch` (Next.js, React, Node, Ollama, Tailwind, Vite, Anthropic SDKs, Claude Code, Supabase) vs last-seen → flags new versions.
- **Outdated deps (weekly):** `npm outdated` / `pip list --outdated` per discovered repo, with majors marked.
- **Staleness (weekly):** repos with no commit in `stale_days` (default 45).
- **AI-ecosystem digest (weekly):** pulls a news feed and has the local LLM surface up to 5 items genuinely worth Brian's attention.

### Safe auto-upgrades (the "auto-apply safe, ask on big" rule)
For repos in `auto_apply_allowlist` (default: the employer-facing `pokemon-drop`), the weekly run:
1. branches `currency/auto-<date>`, runs `npm update` + `npm audit fix` (semver-safe = minor/patch only, **no majors**),
2. reinstalls devDeps and **runs the build** — if it breaks, everything is reverted and nothing is pushed,
3. if green, pushes the branch and **opens a PR** (never commits to `main`).

So safe upgrades arrive **pre-tested, as a one-click PR**; majors/breaking changes are only ever reported for your decision. Set `auto_apply_safe: false` to turn the auto-PR off and just get the report.

### Where output goes
- `comms/currency.md` (daily) and `comms/modernization_report.md` (weekly) — for the dashboard/archive and the brief.
- Urgent items → direct Telegram (update-proof). Weekly summary → Telegram.
- Prepared safe-upgrade PRs → a note in `comms/review/` so the morning brief surfaces them under "review & approve".

## Config — `shared/currency_watch.json`
You maintain three things; the rest is auto-discovered:
- `releases_watch` — the tools/projects whose releases you care about (add the Hermes repo once you have its URL via `hermes_repo`).
- `auto_apply_allowlist` — which repos may get auto-prepared safe-upgrade PRs.
- `github_owner` — for Dependabot lookups.

## Cron (wired)
- `currency` — daily Mon–Sat, light flags.
- `currency-weekly` — Sundays, the deep-dive (`currency_weekly.py`).
Both `--no-agent --deliver local`; the script delivers via its own `telegram_send`, so a quiet day is silent.

## Update rule (inherits VERSIONS.md)
Never blind-merge a major. The agent only auto-prepares **minor/patch** upgrades and only after the build passes. Review major-version PRs by hand, test on the branch's Vercel preview, then merge.

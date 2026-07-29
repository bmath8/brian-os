# Agent 13 — Currency / Modernization
_Keeps the fleet's code, deps, and the AI ecosystem current (and safe)._

- **Owns:** dependency/security freshness across the fleet repos + AI-ecosystem awareness.
- **Why it exists:** stale deps rot and drift; the agent catches them and preps *safe* upgrades. _Solves:_ silent bit-rot, supply-chain risk, "what's new in the stack?"
- **Cadence:** daily Mon–Sat 6:58 AM (`currency`, `currency_agent.py`) + Sun 16:30 deep-dive (`currency-weekly`, `currency_weekly.py`).
- **Tier/model:** free local `qwen3:8b` for release-note triage; deterministic dep scanning.
- **Deliver:** writes `comms/currency.md` + `comms/modernization_report.md` + `state.json` slices; opens **safe** PRs.

## What it does (as implemented)
- Scans all fleet repos for outdated/insecure deps (stdlib + lockfile parsing).
- Watches release feeds (Next.js / React / Node / Ollama / Tailwind / Anthropic SDKs / Claude Code / Supabase).
- Surfaces AI-ecosystem news relevant to Brian's stack.
- Auto-prepares **build-verified SAFE** dependency-upgrade PRs on the employer-facing allowlist — **never touches `main`**; major bumps only reported, not auto-PR'd.
- Dedup ledgers (`comms/.currency_seen.json`, `comms/.currency_discovery_seen.json`).

## Output (writes)
- `comms/currency.md` — the daily currency/modernization section.
- `comms/modernization_report.md` — the weekly deep-dive.
- `state.json` slices `currency`, `currency_weekly`.
- GitHub PRs (minor/patch only; majors reported).

## Hard rule
Never force-push, never touch `main`, never auto-merge. Safe PRs only; majors are reported for human decision.

## Done-when
Daily flag present; weekly report present; safe PRs opened on branches only; no `main` mutation.

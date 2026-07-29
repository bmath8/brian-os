---
name: deploy-runbook
description: Use when Brian wants to deploy, ship, release, or push a Brian OS project to production (Boombox, Giveaway/SONIC-HALO, AI Job Hunter, portfolio, the fleet). Triggers on "deploy...", "ship...", "push to prod", "release...", "go live". Walks the safe pre-flight → deploy → verify → rollback sequence and NEVER deploys without explicit approval.
---

# Deploy Runbook

Ship safely and verifiably. Agents DRAFT and PREPARE a deploy; the actual go-live needs Brian's explicit "yes". Never deploy, spend, or publish on your own.

## 1. Pre-flight (must all pass before proposing deploy)
- **Clean tree:** `git status` clean (or only intended changes); on the right branch.
- **Tests pass:** run the project's test/lint command; paste the real result. Red = stop.
- **Secrets:** no secrets in the diff. `.env` is git-ignored; required env vars exist in the target (compare against `.env.example`). Pre-commit/secret-scan ran.
- **Build works:** the production build/compile succeeds locally first.
- **Migrations:** if the schema changed, the migration is written, reversible, and tested on a copy — never first-run against prod data.

## 2. Find the project's real deploy path (don't invent one)
Look for the project's own deploy doc/config first and follow it:
- Boombox: `docker-compose.yml`, `CI_CD_SETUP.md`, `deploy/`
- AI Job Hunter: `render.yaml`, `README_DEPLOY.md`, `Dockerfile`, alembic migrations
- Giveaway: `DEPLOYMENT.md`, `Dockerfile.*`, `docker-compose.yml`
- Portfolio: static host
If there's no deploy doc, write one as part of this task.

## 3. Deploy (only after Brian approves)
- State exactly what will run and where (which host/service/branch) and what's irreversible.
- Deploy. Capture the output/URL.

## 4. Verify (a deploy isn't done until it's observed working)
- Hit the live health check / key endpoint; confirm a real 200 / expected response.
- Smoke-test the primary user flow on the deployed URL (browser or curl), not just "it built".
- Check logs for errors in the first minutes.

## 5. Rollback ready
- Know the one-command rollback (previous image/commit/release) before deploying.
- If verification fails, roll back first, diagnose second.

## Rules
- Never claim "deployed/shipped/live" without a verification result to back it.
- No deploy without Brian's explicit approval for this specific release.
- Record what was deployed (commit, time, URL) so the next session knows the live state.

## Done when
Pre-flight is green (with pasted evidence), Brian approved, the deploy is verified live by observation, and the live state + rollback step are recorded.

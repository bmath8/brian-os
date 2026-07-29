# eve-eval — illustrative scaffold (NOT deployed, NOT part of the running fleet)

This is a faithful, copy-from starting point for a **Vercel Eve** agent, written to the
real Eve API (see `../EVE_EVALUATION.md` for the full analysis). It is an **evaluation
artifact** — it is not wired into the local Hermes fleet and does not run anywhere yet.

**Recommended first Eve agent: a Job Application Assistant tied to AI Job Hunter.**
Cloud-appropriate (no local-PC data), portfolio-grade, and income-aligned.

## Prerequisites (checked 2026-06-17)
- **Node ≥ 24.** Eve `0.11.4` refuses Node 22 (your current WSL node is v22). Install 24 isolated, without touching your system node:
  ```bash
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  exec bash            # reload shell so nvm loads
  nvm install 24 && nvm use 24
  node --version       # should print v24.x
  ```
- **A (free) Vercel account** — for the AI Gateway model at dev time and for deploy. `eve init` will walk you through login.

## To turn this into a real, runnable agent
```bash
cd /mnt/c/Brian/02_Projects          # (or C:\Brian\02_Projects in PowerShell)
npx eve@latest init ai-job-hunter-agent   # scaffolds, installs deps, opens a TUI
# then copy the files from eve-eval/agent/ into ai-job-hunter-agent/agent/
cd ai-job-hunter-agent
npm run dev                          # local dev UI + HTTP route
```
> The agent's main model runs via Vercel AI Gateway, so `npm run dev` needs you signed in
> (or a provider API key) before it can actually answer. The scaffold below is correct and
> ready; the only manual bits are the Node-24 install, your Vercel login, and answering the
> `eve init` TUI prompts — which is why this is a ~15-min "do it together" step, not unattended.
Hit the session route with a job description:
```bash
curl -X POST http://127.0.0.1:3000/eve/v1/session \
  -H 'content-type: application/json' \
  -d '{"message":"Tailor my application to this JD: <paste job description>"}'
```
Then deploy to Vercel and wire the route into the AI Job Hunter UI.

## Files
- `agent/instructions.md` — the always-on system prompt
- `agent/agent.ts` — model config (via Vercel AI Gateway)
- `agent/tools/ats_keyword_match.ts` — deterministic ATS keyword overlap helper
- `agent/skills/cover_letter.md` — on-demand cover-letter procedure

# Vercel Eve — evaluation for Brian OS (2026-06-17)
_Researched from the real docs (vercel.com/docs/eve, github.com/vercel/eve). Honest fit analysis + a concrete first step + an accurate scaffold under `eve-eval/`._

## What Eve actually is
A **filesystem-first framework for durable cloud AI agents.** You author an agent as files under `agent/`:
- `agent/instructions.md` — always-on system prompt (required)
- `agent/agent.ts` — `defineAgent({ model })`; model strings resolve via **Vercel AI Gateway**
- `agent/tools/*.ts` — one typed tool per file (`defineTool` + zod schema); filename = tool name
- `agent/skills/*` — on-demand procedures/knowledge (markdown) — same idea as our LOOP_AND_SKILLS_DOCTRINE
- `agent/channels/*` — entry points (HTTP, Slack)
- `agent/schedules/*.ts` — cron jobs
- `agent/connections/*` — typed external integrations; `agent/sandbox/*` — isolated compute
Durability via **Vercel Workflow** (event-log replay survives cold starts/redeploys); runs on **Vercel Functions + Fluid Compute**; built-in Agent Runs observability. Start: `npx eve@latest init my-agent`.

## How it maps to our fleet (the good part)
It's almost the same mental model we already built: agents = directories, skills = markdown, cron schedules, human-in-the-loop, sandboxing, tracing. So the concepts transfer 1:1 — we'd feel at home.

## The honest catch (why NOT to migrate the local fleet)
1. **It's cloud, not local.** Eve runs on Vercel Functions and its main model comes from AI Gateway (cloud, e.g. `anthropic/claude-sonnet-4.6`). Our fleet's whole point is **free local qwen3:8b**. Moving the daily brief/watchdog/learning to Eve means paying per call for work that's currently $0.
2. **It can't see your PC.** The brief/backup/watchdog read `C:\Users...\Harmony`, `comms/`, host RAM, Ollama on localhost. A Vercel Function in the cloud cannot read your local drive or your host's Ollama without exposing them publicly (a tunnel) — which defeats the locality and adds attack surface.
3. **Telegram isn't a built-in channel** (HTTP + Slack are). You'd add an HTTP channel + a Telegram webhook.

**Conclusion: keep the local Hermes fleet exactly as it is** for the always-on, free, private, PC-bound tasks. That's the right tool for that job.

## Where Eve IS the right tool for you (high value)
A **cloud-appropriate, public-facing agent** with no local-data dependency — ideally tied to your flagship **AI Job Hunter**:

> **"Job Application Assistant" (Eve agent):** paste a job description (+ your resume on file) → it returns a tailored resume bullet set, an ATS keyword check, and a cover-letter draft. HTTP channel (callable from the AI Job Hunter UI), schedules optional, model via AI Gateway (Sonnet/Opus for the final draft — exactly Tier-3 in our ROUTING doctrine).

Why this is the right first Eve project:
- **Portfolio gold:** "I built and deployed a durable agent on Vercel's Eve, wired to my AI job-search app" is a strong, current résumé line — and it's *deployed and clickable*, which recruiters love.
- **Genuinely suits Eve:** cloud model, HTTP entry point, no local-PC data, benefits from durability/observability.
- **Reuses your real work:** the tailoring/ATS logic already exists in AI Job Hunter (the part we said to showcase, not the auto-apply).
- **Income-aligned:** it's literally part of the job-search engine, which is goal #1.

## Cost reality
Eve itself is open-source/free; you pay for Vercel Functions + the AI Gateway model calls. A job-tailoring agent is bursty and low-volume (you, a few times a day) → cents. Use a cheap Tier-A model for drafts (Kimi K2.7 / Gemini 3.1 Pro per our cloud ladder) and reserve Opus 4.8 for the final "going out with my name on it" pass.

## Concrete next step (when you want to, ~1 hr) — prerequisites verified 2026-06-17
**Two quick prereqs (do-together step, not unattended):** Eve needs **Node ≥ 24** (your WSL has v22 → install 24 via `nvm`, see `eve-eval/README.md`) and a **Vercel login** (AI Gateway model + deploy). Then:
1. `cd C:\Brian\02_Projects` then `npx eve@latest init ai-job-hunter-agent`.
2. Drop in the starter files in **`eve-eval/`** (this folder) — `instructions.md`, `agent.ts`, and the `tailor_application` tool — as your starting point.
3. `npm run dev`, hit the local HTTP route with a job description, iterate.
4. Deploy to Vercel; wire the route into the AI Job Hunter UI.
5. Add it to your portfolio/README as a live demo.

A faithful **minimal scaffold** is in `eve-eval/` so you can see exactly what the files look like (it's an illustration to copy from, not wired into the running fleet).

## Decision
- **Local fleet:** unchanged (free/local/private — correct as built).
- **Eve:** adopt for ONE new cloud agent tied to AI Job Hunter — portfolio + income value, and the right use of the tool. Not a migration; an addition.

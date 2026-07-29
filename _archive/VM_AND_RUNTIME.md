# Execution Runtime & Isolation
_How the fleet actually RUNS — sandboxed agents, host GPU, local models first. Last updated 2026-06-16._

## The problem this solves
1. Claude-scheduled tasks run on Claude's servers, not Brian's free local models. To honor "open/free models first," agents must execute on Brian's machine.
2. Autonomous agents run shell commands, browser automation, and hold credentials — a real security surface. Brian wants them isolated so a bad agent or prompt-injection can't compromise the host PC.

## The design: split the layers
```
 ┌───────────────────────────── HOST (Windows 11) ─────────────────────────────┐
 │  Ollama  →  localhost:11434   (GPU: RTX 4070 Super, native speed)            │
 │  • Just a model server. Does NOT run shell/browser/credentials = low risk.   │
 │                                                                              │
 │   ┌──────────── SANDBOX (WSL2 or VM) ────────────┐                           │
 │   │  Agent runtime: Hermes Agent and/or OpenClaw │                           │
 │   │  • runs shell, browser (Playwright), files   │  ── calls models ──▶ host │
 │   │  • holds API keys / chat tokens              │     over localhost net    │
 │   │  • the fleet: router.py, comms/, agent skills│                           │
 │   │  • messages Brian (Telegram/Slack/email)     │                           │
 │   └──────────────────────────────────────────────┘                          │
 └──────────────────────────────────────────────────────────────────────────────┘
```
**Why this split:** full-VM isolation normally blocks easy GPU access. By keeping Ollama (inference only, low-risk) on the host and sandboxing only the agents (high-risk), Brian gets free local GPU models AND containment. The sandbox only needs network access to the model endpoint.

## Isolation options (Windows 11)
| Option | Isolation | GPU for local models | Verdict |
|---|---|---|---|
| **WSL2** (Linux under Win) | Medium (separate userspace, shared kernel) | Native CUDA passthrough — fast | **Recommended start.** Easiest, near-native, agents isolated from host files unless mounted. |
| **Hyper-V VM** (Win Pro) | Strong | Hard (GPU-PV fiddly) → agents call host Ollama over net | Best if max isolation wanted; pair with host Ollama. |
| **VirtualBox/VMware Linux VM** | Strong | Hard | Same as Hyper-V; heavier. |
| **Windows Sandbox** | Strong but disposable (resets) | No | Bad for a persistent agent — skip. |

**Recommendation:** host Ollama + agents in **WSL2** to start (free, fast, isolated enough). Move the agent layer into a dedicated Hyper-V VM later if you want airtight isolation — the host-Ollama design means that swap needs no rework.

## Runtime choice: Hermes vs OpenClaw
Both are open-source, model-agnostic (use Ollama), message you on chat platforms, and share the agentskills.io skill standard — so fleet skills are portable between them.

| | **Hermes Agent** | **OpenClaw** |
|---|---|---|
| Best at | built-in cron scheduler, multi-platform message fan-out, persistent memory | heavy browser automation (Playwright), 100+ prebuilt skills, shell ops |
| Fits | **the daily briefing + reminders + "tell me X"** | **do-things-for-me** (job board scraping, form-filling, research) |
| Start here for | Agent #1 Chief of Staff briefing → your phone | Agent #2 Job Hunter (browser-heavy) |

**Recommendation:** start with **Hermes** for the briefing (its cron + messaging is the exact fit), add **OpenClaw** later for browser-heavy jobs. They can coexist and share skills.

## Security guardrails for this layer (on top of GUARDRAILS.md)
- Agents live in the sandbox; **host files are reachable only if explicitly mounted** — mount Harmony read-mostly, keep `C:\Brian` code separate.
- **Credentials minimal & scoped:** only the API keys / chat tokens an agent needs, stored in the sandbox, never the host password manager.
- **Yellow/Red actions still require Brian's approval** even though the agent is sandboxed — isolation limits damage, it doesn't grant autonomy to send/spend/delete.
- Local-first per [shared/ROUTING.md](shared/ROUTING.md): cloud keys only added when a task escalates.

## Migration: Claude schedule → local runtime
The Claude scheduled task `fleet-chief-of-staff-daily-brief` is an **interim**. Once Hermes runs the briefing locally and messages Brian, retire the Claude task (or keep as backup). Same prompt (`prompts/daily_briefing_agent.md`) becomes a Hermes skill/cron job.

## Locked decisions (2026-06-16)
- **Isolation (long-term-best):** permanent split — **Ollama stays on host** (GPU). **Agents sandboxed.** Start in **WSL2** now (fast, GPU-adjacent, isolated), graduate the agent layer to a **dedicated always-on runner** (Hyper-V VM now → mini-PC when income allows) so the fleet runs 24/7 independent of the laptop. Host-Ollama design means that upgrade needs zero rework.
- **Runtime:** **Both** — Hermes (briefing, cron, Telegram fan-out, memory) + OpenClaw (browser automation, heavy "do-it" jobs). Stand up Hermes first.
- **Channel:** **Telegram** — one bot token, phone + desktop, free, native in both tools.
- **Models:** local-first per ROUTING — pull `qwen3:14b` + `qwen3:8b` + `deepseek-r1:14b` (pending Brian's go on the ~28 GB download).

## Setup order (once decisions are made)
1. Enable WSL2 (+ Ubuntu) — or provision the chosen VM.
2. Confirm host Ollama is reachable from the sandbox (`curl host:11434/api/tags`).
3. Install the chosen runtime (Hermes first) inside the sandbox; point it at host Ollama.
4. Connect ONE message channel (Telegram bot is quickest) so it can reach Brian.
5. Port the daily-brief prompt in as a cron job; verify a test run lands on Brian's phone.
6. Add OpenClaw + the Job Hunter job in phase 2.

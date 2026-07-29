# Brian OS — Master Status (done vs. to-do)
_Single source of truth across the whole project. Last updated 2026-07-28 (audit: claims re-verified against live system)._

> **Doc discipline (2026-07-28):** this repo had accumulated **8 audit documents**, four
> named `MASTER_IMPROVEMENT_AUDIT` (06-20, 06-21, 07-06, 07-11) — while the calendar agent
> sat dead and no `requirements.txt` existed. Findings now get **fixed and folded into this
> file**. Do not create audit doc #9.

## ✅ DONE & VERIFIED

### 2026-07-28 — audit: verified claims against reality, fixed what was actually broken
Method: ignored status docs, checked live processes / log timestamps / actual command output.

- [x] **Calendar agent was DEAD and nothing caught it.** `comms/calendar.md` contained
      `(calendar fetch failed: No module named 'icalendar')`. Root cause: the fleet had
      **no `requirements.txt` at all** — agent deps were undeclared and unverified.
      Fixed: installed `icalendar` + `recurring_ical_events` into the venv that actually
      runs cron (`%LOCALAPPDATA%\hermes\hermes-agent\venv`). Verified: agent now returns
      real events and logs `calendar | ok | 1 today`.
- [x] **`runtime/requirements.txt` created** — REQUIRED / DEV / OPTIONAL blocks, documenting
      that `caldav` (iCloud path) and `fsrs` (draft, fallback-safe) are absent *on purpose*.
- [x] **`boot_smoke.py` now has a `Deps` check** so this class of failure pages Brian on the
      next boot/revive instead of rotting silently. Verified it can actually FAIL (negative
      test with a bogus module), not just pass.
- [x] **Dashboard was blind to 9 working agents.** 25 cron jobs live, but only 14 agents
      hand-wrote a state slice → `state.json` knew 16 → dashboard rendered "16 agents". A
      silently dead agent looked identical to one that just never publishes state.
      Fixed: `fleet_common.state_heartbeat()`, called from `log_run()`, so every agent is
      visible for free. **Merges** (never replaces) so rich slices survive; `STATE_ALIASES`
      maps drifted names (`gig_scanner`→`gigs`, `outcome_learner`→`outcomes`) so no dupes.
- [x] **`process_guardian.ps1` gateway metric was useless.** It counted raw processes, so a
      healthy gateway (venv launcher → `.hermes-runtime` child = a parent→child pair) read
      as `gateway=2` forever — meaning a *real* duplicate would have been indistinguishable
      from normal. Now counts distinct process **trees**; verified `gateway=1`.
- [x] **Test suite: 81 passing.** Was 79 + 1 silent load error: `tests/test_powershell.py`
      imports `pytest`, which was never installed, so the PowerShell infra tests
      (guardian/keepalive) had **never run here**. Installed; suite is green.
- [x] **Security check:** no secrets tracked in `brian-os-fleet`, `ai-job-hunter`, or
      `03_Career` (only an intended `.env.example`). Open item: Hermes' own vendored deps
      carry HIGH advisories (`httplib2 0.31.2`, `mcp 1.26.0`, `pillow 12.2.0`) — not our
      code; fix by upgrading Hermes, not by patching its venv.

**Verified as correct-by-design — do NOT "fix" these:** `currency` logging `alert` (means
findings exist, not a crash); two `hermes_cli.*gateway` processes (healthy parent→child pair);
`guardian.log` at ~450 KB (self-rotates at 500 KB); `ceo_report`/`model_review`/`skill_miner`/
`feedback`/`research`/`wiki` looking "stale" (weekly/monthly cadences, running correctly).

### 2026-06-19 — migrated off WSL to NATIVE WINDOWS + applied research + cleanup
- [x] **Root-caused the overnight outage:** WSL 2.6.1.0 VM-teardown bug (microsoft/WSL #13416).
- [x] **Migrated the whole fleet to native Windows Hermes v0.17.0** (no WSL). Ollama now localhost; the WSL failure class is gone. WSL kept disabled as fallback. 49 tests pass on native Windows too.
- [x] Native gateway live (Telegram + cron scheduler); Startup **keepalive** for auto-start + self-heal.
- [x] OS-aware `fleet_common` (paths/localhost/UTF-8); cross-platform `backup_harmony.py`; `hermes doctor` in the watchdog.
- [x] Fixed native command conflicts → `/fleet /addtask /approvedraft /rejectdraft /grade /snooze`.
- [x] **8-skill chat-agent library** (job-application, outreach, interview-prep, follow-up, project-showcase, build-in-public, learn-and-retain, weekly-reflection).
- [x] **Nous Portal logged in** (escalation only; local qwen3:8b stays default).
- [x] Applied the "Executive Summary" research (`PDF_RESEARCH_APPLIED_2026-06-19.md`) — it validated the architecture.
- [x] **Cleanup:** dead WSL scripts → `runtime/_wsl_legacy/`; obsolete WSL docs + Eve eval → `_archive/`; README + CURRENT_STATE rewritten to native reality.



### 2026-06-18 — deep-audit fixes (branch `deep-audit-fixes-2026-06-18`, tested, NOT yet deployed)
- [x] Shared core `runtime/fleet_common.py`: central config, **atomic+locked `state.json`** (race fixed), resilient `ollama_generate` (timeout+retry+fallback+JSON-schema), `model_for` gate wired into the real path, header-aware `tracker_cell`, `age_needs`, idempotency, uniform logging.
- [x] All 9 agents refactored onto it (+`main()` guards). Brief now **persists** to `comms/daily_brief.md`+history. Overnight worker uses a **separate critic** (`deepseek-r1:14b`) + deterministic guardrail checks.
- [x] `shared/router.py`+`models.json`: removed dead `gemma4:26b`; registry now honest.
- [x] **Test suite + GitHub Actions CI** (`tests/`, 28 tests, stdlib-only). First automated regression net.
- [x] Observability: `runtime/log_analyzer.py` (→`comms/fleet_health.md`) + `runtime/build_dashboard.py` (→`comms/dashboard.html`).
- [x] Docs: `FLEET_DEEP_AUDIT_2026-06-18.md`, `IMPROVEMENTS_2026-06-18.md`, `DEPLOY_NOTES_2026-06-18.md`; blueprint agent count fixed (10).
- [ ] **Brian to run:** review branch → `tests` → merge → `runtime/deploy_to_hermes.sh` → optional cron for the 2 ops agents (see DEPLOY_NOTES). Deploy/push deliberately left to you (Yellow).

### Fleet — reliability & infrastructure
- [x] Deep line-by-line audit (`AUDIT_2026-06-17.md`); gaps G1–G19 all closed.
- [x] Gateway auto-start + reboot survival CONFIRMED. _(Corrected 2026-07-28: this line
      previously said "systemd --user service + linger" — leftover from the pre-2026-06-19
      WSL era and contradicted by the native-Windows migration recorded above. Auto-start is
      the Startup keepalive (`BrianOS-Keepalive.vbs` → `fleet_keepalive_loop.ps1`); there is
      no systemd on this box.)_
- [x] Self-heal hardened + **systemd-aware** (no duplicate gateway / Telegram conflict).
- [x] Ollama self-heal (`ensure_ollama.ps1`); host bound `0.0.0.0:11434`.
- [x] `run_log.md` audit trail written by every agent.
- [x] Security verified: no secrets in git history; secrets only in gitignored `.env`/`sandbox`.
- [x] Backups: Harmony mirror nightly; fleet pushed to private GitHub `bmath8/brian-os-fleet`.
- [x] Ops tool: `runtime/fleet_status.sh` (one-shot health dashboard).

### Fleet — 25 cron agents (all local/free on qwen3:8b)
- [x] Chief of Staff (daily brief 7:00 → Telegram)
- [x] System Watchdog (4h, self-heal)
- [x] Overnight Worker (2:00, self-verify loop)
- [x] Learning (6:45, recall)
- [x] Scout (6:40, free DuckDuckGo discovery)
- [x] Finance (6:50) · Health (6:52) — read Harmony trackers, never invent data
- [x] Weekly Review (Sun 17:00 → Harmony + Telegram)
- [x] Harmony Backup (1:30) · Model Review (monthly)
- [x] Brief now shows: needs / review / job-hunt # / Scout / priorities / System / RAM / Money&Health / Recall

### Models
- [x] `qwen3:8b` default; `qwen3:14b` + `deepseek-r1:14b` for post-RAM; llama3 removed (redundant).
- [x] `models.json` registry refreshed; router fixed (host-IP, default); VRAM-gated routing via `fleet_common.model_for()` (the old `safe_model.py` RAM floor was retired 2026-07-15).
- [x] Monthly model-review + `MODELS_AND_TOOLS_REVIEW` (cloud ladder: DeepSeek/Kimi/GLM/Opus).

### AI Job Hunter (flagship)
- [x] **Free-first web reader** (`services/firecrawl_jobs.py`): DuckDuckGo search + local scrape =$0;
      **Crawl4AI live** (free, unlimited, JS) via isolated 3.11 sidecar venv + subprocess bridge;
      **Firecrawl hard-capped** (default 100/mo) — cannot overspend. Wired into the aggregator.
- [x] Launcher `.bat` fixed (pointed at a dead OneDrive path → `C:\Brian`).
- [x] Pushed to `bmath8/ai-job-hunter`. `.env` (key) gitignored; cap tracked on disk.

### Strategy & docs
- [x] `BrianOS_Standards/TECH_STACK_DECISIONS.md`: per-project hosting, scraping-levels ladder, tool-adoption filter.
- [x] Tools judged: Firecrawl ✅adopted, Crawl4AI ✅live, Omma ▶portfolio, Photon/Factory ✗bookmarked.
- [x] Vercel Eve evaluated + scaffold (`eve-eval/`).
- [x] Disk cleanup (~8 GB reclaimed); ~80 GB free.

## 🟡 NEEDS BRIAN (can't be done without you — quick)
- [ ] **Confirm Firecrawl is on the Free plan with NO card** (ironclad no-charge guarantee; code cap is backup).
- [ ] **Fill tracker numbers**: job apps as you send them; finance monthly expenses (→ real runway); health weekly log.
- [ ] **Reply to @CK08Bot** now and then (two-way chat).
- [ ] **Portfolio polish with Omma** (free tier) — 30–60 min creative step.

## ▶ OPTIONAL NEXT BUILDS (my control, on request)
- [ ] Vercel Eve job-application agent — do-together (needs Node 24 + your Vercel login).
- [ ] Wire the reader into the live CLI `search` command end-to-end (today it's in the aggregator + example).
- [ ] Git-init + back up `BrianOS_Standards` to a private repo (currently local-only).

## 🖥️ HARDWARE (the #1 unlock)
- [ ] **16 GB → 64 GB DDR5 RAM** (optional). More VRAM headroom for bigger local models. Model gating is `fleet_common.model_for()` (VRAM-based); the old `safe_model.py` RAM-gate was retired 2026-07-15 (dead + WSL-path bug).

> Status: the system is **operational, reliable, free, and documented.** Everything in the plan is
> built except the items above, which are either yours (data/accounts) or deliberate future builds.

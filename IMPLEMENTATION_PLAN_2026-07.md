# Implementation Plan — all 71 Next-Level items (2026-07-11)

Every item from NEXT_LEVEL_IDEAS_2026-07-11.md, sequenced into 10 phases by
dependency and leverage. Each phase = one working session (Cowork session with me,
or your own time where marked **YOU**). Rules that govern every phase are at the
bottom. Item numbers (#) refer to the ideas doc.

**Cadence:** one phase per session, phases 0-2 this weekend, then ~3/week.
**Tracking:** check items off HERE; the Sunday weekly review reads this file's
unchecked count so progress is visible in Telegram automatically.

---

## Phase 0 — TONIGHT (YOU, ~45 min) — unblocks everything else
- [ ] #28 Reboot (clears Claude file handles + reclaims hibernate's 6.3 GB)
- [ ] Disk deletions you planned (Steam/Epic decision, .cache/.codex, Docker if unused)
- [ ] #8 Log your real applications so far into Job_Tracker.md pipeline rows
      (5-10 rows unblinds outcome-learner — 15 minutes, highest ROI of anything here)
- [ ] Approve or reject the 2 pending drafts (comms/review/) — starts the QLoRA counter
- [ ] #47 Rotate ai-job-hunter .secret.key (its own rotation path)

**Acceptance:** disk >100 GB free, outcomes.md shows real data Sunday, review queue empty.

## Phase 1 — Session A: The Cowork bridges (me, ~2h) — oldest gap dies
- [ ] #1 Gmail→brief bridge: scheduled Cowork task 6:45am → comms/gmail.md
      (redacted subjects/senders of unread-important; daily_brief composes it in)
- [ ] #2 Todoist→brief bridge: same pattern → comms/todoist.md (today + overdue)
- [ ] #6 Vercel monitor: weekly scheduled task → deployment status + runtime errors
      of portfolio/pokemon-drop → comms/currency.md section
- [ ] #45 Brief includes gig matches ≥5 (5-line daily_brief change)
- [ ] #41 Phone-first brief format (scoreboard/ONE-thing/needs in first 3 lines)
- [ ] Fleet side: daily_brief.py reads the two new comms files (fenced as untrusted)

**Depends on:** nothing. **Risk:** low (additive files; brief degrades gracefully
if a bridge misses a morning). **Acceptance:** tomorrow's 7am brief shows real
Gmail + Todoist data; test suite green.

## Phase 2 — Session B: Income pipeline (me, ~2h) — wake up to applications
- [ ] #7 Auto-tailor: scout/gig match ≥ threshold → auto-queue /tailor for top 3
      → overnight worker drafts kits → review queue by morning
- [ ] #12 Application SLA guard: alert when a 48h-old strong match has no
      Job_Tracker row
- [ ] #23 Verification gates on scout + gig-scanner output (dead-link check,
      dedupe, remote/level sanity pass) — Berman loop pattern
- [ ] #64 Fresh-eyes-until-clean revision loop in overnight worker (capped at 3
      rounds, exit when a pass finds nothing)
- [ ] #65 Queue dependency headers (deps: line) so multi-step jobs execute in order

**Depends on:** Phase 0 (logged apps make thresholds meaningful). **Acceptance:**
one full cycle observed: match → queued → drafted overnight → in review queue,
81+ tests green.

## Phase 3 — Session C: Observability spine (me, ~1.5h)
- [ ] #15 log_trajectory wired into all 15+ agents (agent, model, status, ms)
- [ ] #16 Draft-quality scoreboard by type (approve/reject per tailor/followup/proposal)
- [ ] #24 Guardian weekly report line in Sunday review (reaped/RAM/disk trends)
- [ ] #25 Prompt regression eval hook: eval_models.py baseline stored; deploy_fleet.ps1
      warns when a drafting prompt changed without an eval run
- [ ] #27 Token diet: structured-output (fmt=json) for remaining free-text agent calls
- [ ] #43 /done command (what the fleet did today, from run_log)
- [ ] #18 /why command (signals behind today's ONE thing)

**Acceptance:** trajectory.jsonl shows every agent within 24h; CEO report's fallback
becomes unnecessary; /done and /why answer live.

## Phase 4 — Session D: Interview fast path (me, ~2h) — highest-stakes emails
- [ ] #4 Inbox triage: scheduled Cowork task labels job-hunt emails (invite /
      recruiter / rejection / other) → comms/gmail.md gains a priority section →
      urgent Telegram ping on INVITE class
- [ ] #9 Invite → auto-/prep: career agent sees invite flag → queues /prep with
      company+role → kit in review queue same day
- [ ] #10 Company dossier: pipeline row hits "screen" → overnight one-pager
      (web fetch + job-search MCP company data)
- [ ] #5 Calendar write-back: prep blocks proposed via Telegram approval →
      Cowork task creates the event
- [ ] #11 Referral-path finder v1: networking.md + GitHub follows cross-check
      against target companies; brief suggests one outreach/day

**Depends on:** Phase 1 bridges. **Risk:** medium (email classification errors) —
mitigation: triage only LABELS, never archives/replies; invite pings link the
actual email. **Acceptance:** a test invite email round-trips to a Telegram ping
+ prep kit.

## Phase 5 — Session E: Skills & doctrine upgrades (me, ~1.5h)
- [ ] #26/#67 Karpathy guardrails preamble → overnight worker + /code + /tailor
- [ ] #66 Upgrade job-application + voice-match skills to rich directories
      (SKILL.md + references + examples, progressive disclosure)
- [ ] #35 Point skill-miner cron at anthropics/skills + awesome-claude-skills repos
- [ ] #68 Mine Berman Loop Library → adopt 2 loops with explicit stop criteria
- [ ] #63 /plan command: local draft plan → redacted cloud critique (router) →
      local merge; repeat rounds on demand (doodlestein plan-space loop)
- [ ] #70 Grouped-commit prompt into deploy workflow + AGENTS.md files
- [ ] #40 x-research-skill installed for the X watchlist digestion

**Acceptance:** /plan works end-to-end on a real plan; two upgraded skill dirs
deployed; skill-miner's next Sunday run reports from the new sources.

## Phase 6 — Session F: Life-OS + UX (me, ~1.5h)
- [ ] #53 Runway auto-calc (one weekly balance+burn line → "runway: N weeks" in brief)
- [ ] #54 Health streak in scoreboard (mirror application-streak code)
- [ ] #55 SRS cards auto-generated from applied-to job tech (2/week)
- [ ] #20 Tracker nudges: weekly Telegram ask, reply /log writes the tracker
- [ ] #56 Personal-project hour suggestion when weekly app target is met
- [ ] #57 Relationships cadence tracker (family/friends, private file)
- [ ] #42 Dashboard red banner for income-critical needs
- [ ] #44 2-way Sunday review (3 questions, replies feed feedback.py)
- [ ] #46 Open WebUI presets for tailor/prep/code

**Acceptance:** brief shows runway + health streak; /log round-trips; Sunday
review asks and records.

## Phase 7 — Session G: Projects & portfolio (me + YOU decide, ~2h)
- [ ] #60 Portfolio case study: "24-agent autonomous fleet" page drafted from the
      audit docs (I draft; you approve before it goes on the password-gated site)
- [ ] #59 pokemon-drop + portfolio uptime check in daily currency run
- [ ] #62 AGENTS.md for viral-forge, giveaway-app, boombox-v5
- [ ] #58 ai-job-hunter ↔ fleet seam decision documented in both AGENTS.md
      (**YOU** decide the seam; I write it up)
- [ ] #61 Supabase advisors run on boombox (security/perf lints via connector)
- [ ] #14 viral-forge + giveaway-app verdict: ship / park / archive (**YOU**)
- [ ] #13 Launch runbook skill for pokemon-drop + portfolio (ready-to-fire)

**Acceptance:** case study draft in review queue; uptime checks live; three new
AGENTS.md committed.

## Phase 8 — Session H: Security wave 2 (me, ~1h)
- [ ] #49 git filter-repo purge of old .db/.secret.key in ai-job-hunter history
      (after #47 rotation; repo stays private meanwhile)
- [ ] #48 hermes secrets → Bitwarden/1Password migration (**YOU** pick the manager,
      ~10 min together)
- [ ] #52 windows-mcp python children added to guardian dup patterns explicitly
- [ ] #50 Second backup target on the external drive (**YOU** buy it — same drive
      solves Steam; I wire the robocopy job)
- [ ] #51 Monthly restore-test cron (3 random files diffed mirror vs source)

**Acceptance:** history clean, secrets out of plaintext, restore-test passes.

## Phase 9 — Session I: Perf experiments (me, ~1.5h, measure-first)
- [ ] #29 Embed-cache hash-skip in memory_index
- [ ] #30 Brief synthesis cache (skip regen when signals unchanged)
- [ ] #33 Speculative decoding on DENSE 8b (0.6b draft model, llama.cpp toolkit
      already installed) — adopt only if ≥1.3× on eval_models.py
- [ ] #32 keep_alive weekday-daytime experiment (30m → 10m, watch warm-start regressions)
- [ ] #34 DDR5 price watcher in currency agent (your threshold: set it)
- [ ] #31 Qwen3.5 eval SAME DAY the Ollama build lands (currency already flags it)

**Acceptance:** each experiment has a number attached; losers reverted same session.

## Phase 10 — QLoRA self-learning (me, GATED — do not start early)
- [ ] Gate: 30+ approved drafts in comms/review/approved/ (check: Sunday review
      counts it; Phase 0 + daily approvals feed it)
- [ ] Execute FINETUNE_RUNBOOK.md: dataset build → overnight train (~90 min) →
      brian-8b in Ollama → A/B eval → adopt only if it wins
- [ ] #71 Outcome data as JSONL alongside markdown (agent-first tooling)

## Continuous (no session — habits + already-running automation)
- **YOU, daily (~10 min):** approve/reject drafts · log every application ·
  reply to the weekly tracker nudge. Every learning loop feeds on this.
- **Fleet, automatic:** currency agent watches releases (Qwen3.5, Ollama, Hermes)
  · skill-miner Sundays · outcome-learner Sundays · CEO report monthly.
- #69 Principle (not a task): manually work any NEW workflow ~10 times before
  we automate it.
- #17 wiki weekly diff + #19 snooze-with-reason + #21 voice notes + #22 /focus +
  #36-38 Claude Code plugins (Superpowers/Context7/Claude-Mem) — batch into the
  first session that finishes early; none block anything.
- #3 job-search MCP scout upgrade — fold into Phase 1 if session time allows,
  else Phase 4.

## Standing rules for every phase (non-negotiable)
1. Tests green before AND after; new features ship with a test where testable.
2. Deploy from repo → %LOCALAPPDATA%\hermes\scripts; commit + push same session.
3. Draft-only guardrail: nothing sends/spends/deletes without your approval.
4. External content fenced (wrap_untrusted) — includes Gmail/Todoist bridge files.
5. Redact-first before anything cloud-bound (BRIAN_PII is live).
6. Every loop gets a verification gate + stop criteria before it ships.
7. Measure, don't vibe: experiments carry numbers; losers reverted same session.
8. One phase per session; finish and verify before starting the next.
9. Read fleet logs from copies in Claude sessions (handle-lock lesson).
10. Update this file's checkboxes + CURRENT_STATE.md at the end of every phase.

## Dependency map (why this order)
Phase 0 → unblocks 2 (thresholds), 10 (approvals) and disk headroom for 9.
Phase 1 → unblocks 4 (triage needs the Gmail bridge).
Phase 3 → makes 5-9's changes measurable (trajectory + eval baselines first
would be ideal, but 1-2 outrank it because income > telemetry).
Phase 10 gate is data volume, not calendar — could arrive before Phase 8.

**Start:** say "start phase 1" in a fresh session (or this one).

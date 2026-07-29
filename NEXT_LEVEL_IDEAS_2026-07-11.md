# Next-Level Ideas — 2026-07-11 (the full arsenal)

Every high-impact feature, improvement, and optimization I can find for your setup,
ranked inside each category. Tags: [★ = do first] [E = easy <1h] [M = medium] [H = heavy].
Items marked (B) need only your go-ahead — I can build them in a session like this one.

## 1. THE BIG UNLOCK — your Cowork connectors are an untapped bridge

Your fleet's #1 gap since June 21 is "Gmail + Todoist into the brief, gated on
credentials." But THIS Cowork session already has authorized connectors for **Gmail,
Google Calendar, Todoist**, a **job-search MCP** (search_jobs + get_resume + company
data), **Vercel, Supabase, Notion, Spotify, Chrome, Windows control**. No API keys
needed — the auth already exists here.

1. [★E](B) **Gmail→brief bridge**: a scheduled Cowork task (6:45am) reads unread/
   important via the Gmail connector, writes a redacted summary to the fleet's
   comms/gmail.md — daily_brief picks it up like any blackboard file. Closes the
   3-week-old gap with ZERO fleet code.
2. [★E](B) **Todoist→brief bridge**: same pattern — today's tasks + overdue into
   comms/todoist.md. Your brief finally knows your real task list.
3. [★M](B) **Job-search MCP → scout upgrade**: the connector's search_jobs returns
   structured listings with company data. A scheduled task can feed BETTER listings
   into comms/scout.md than the fleet's RSS scraping — with salary/company intel.
4. [M](B) **Inbox triage agent**: scheduled Cowork task labels job-hunt emails
   (interview invites! recruiter pings!) and alerts the fleet — an interview invite
   sitting unread for 6 hours is a lost income event. THE highest-stakes email class.
5. [M](B) **Calendar write-back**: fleet suggests interview-prep blocks; a Cowork
   task actually creates the calendar events (with your approval via Telegram).
6. [E](B) **Vercel deploy monitor**: scheduled task checks your deployments/runtime
   errors weekly → comms/currency.md (your portfolio being DOWN during a job hunt is
   a silent disaster; nothing watches it today).

## 2. Income accelerators (the mission)

7. [★M](B) **Auto-tailor pipeline**: scout/gig-scanner matches ≥ threshold →
   auto-queue /tailor for the top 3 overnight → morning brief delivers ready
   application kits. You wake up to drafted applications, not just listings.
8. [★E] **Log every application in Job_Tracker** — outcome-learner shipped today is
   BLIND until ~5+ rows exist. The single highest-ROI manual habit.
9. [M](B) **Interview-invite fast path**: email triage (#4) detects an invite →
   /prep runs automatically → prep kit in review queue before you've replied.
10. [M](B) **Company-research dossier**: on any pipeline row reaching "screen",
    overnight worker builds a one-pager (product, stack, recent news, likely
    questions) from web fetch + job-search MCP company data.
11. [M](B) **Referral-path finder**: for each target company, check your networking
    log + GitHub follows for warm paths; brief suggests ONE outreach/day.
12. [E](B) **Application SLA guard**: career agent alerts if a scout/gig match older
    than 48h was never applied to — fresh listings convert far better.
13. [H] **Portfolio launch runbook as a skill**: pokemon-drop + portfolio are
    password-gated by design; pre-build the unlock+index+post sequence so the day
    you say "launch," it's one command. (Was roadmap #18, still unbuilt.)
14. [M](B) **viral-forge + giveaway-app**: currency agent covers deps, but neither
    has an AGENTS.md nor appears in any income plan — decide: ship, park, or archive.
    An archived project is free focus.

## 3. Fleet features / new agents

15. [★M](B) **Wire log_trajectory into all agents** (today only the router logs it) —
    unlocks real per-agent evals, the CEO report's full power, and future tool-tuning
    data. ~10 lines per agent.
16. [M](B) **Draft-quality scoreboard**: track approve/reject ratio per draft TYPE
    (tailor/followup/proposal) — tells you which drafting prompts need work, and
    feeds the QLoRA dataset gate (30+ approved).
17. [M](B) **Weekly "what changed in my world" diff**: wiki agent exists; add a diff
    pass — what changed across all topic pages this week, 5 bullets in Sunday review.
18. [E](B) **/why command**: Telegram command that explains the brief's ONE thing —
    "why this today?" with the signals that drove it. Trust through transparency.
19. [M](B) **Snooze-with-reason + auto-unsnooze**: snoozes currently expire silently;
    resurface with "you snoozed this 7d ago, still relevant?"
20. [M](B) **Health/finance tracker nudges**: both agents report "blank tracker"
    chronically — add a once-weekly Telegram ask ("reply /log weight 180") that
    writes the tracker for you. Data entry is the bottleneck, not analysis.
21. [H] **Voice interface**: Hermes supports Telegram voice notes → whisper.cpp local
    transcription → command grammar. Log networking touches while driving.
22. [M](B) **Spotify focus trigger**: Windows-MCP + Spotify connector — a /focus
    command that starts your deep-work playlist + sets a 50-min timer + mutes
    non-urgent fleet pings. Cheap, real behavior lever.

## 4. Loops & verification (the doctrine)

23. [★E](B) **Verification gate for scout/gig output**: dedupe + dead-link check +
    "is this actually remote/junior-friendly?" LLM pass before it hits the brief —
    the overnight worker has gates; the scanners still don't.
24. [E](B) **Weekly guardian report line** in Sunday review: processes reaped,
    RAM trend, disk trend — the cascade class becomes a weekly-visible metric.
25. [M](B) **Prompt regression evals**: your 5-task eval harness exists
    (eval_models.py) — run it automatically after ANY prompt edit in a drafting
    agent, compare to stored baseline. Catches "improved the prompt, broke the output."
26. [M] **Karpathy-guidelines skill** (144k stars): 4 behavioral principles (no
    silent assumptions, no over-engineering, no orthogonal changes) — add as a
    fleet-wide preamble for the overnight worker + /code. Free quality.
27. [E](B) **Caveman-style token diet for cron agents**: strip narration from agent
    LLM calls (structured output everywhere) — faster runs, less VRAM time.

## 5. Model / performance (post-benchmark reality)

28. [★E] **Reboot tonight** — clears the Claude read-handles, reclaims hibernate's
    6.3 GB, finishes the cleanup you started.
29. [E](B) **Embed-cache for RAG**: memory_index re-embeds unchanged chunks nightly;
    hash-skip unchanged files → faster 1:20am run, less GPU wake.
30. [M](B) **Distill the brief's synthesis**: the 7am brief uses 8b for synthesis;
    cache the last 7 days' ONE-things and skip regeneration when signals are
    unchanged (weekend mornings are often identical).
31. [M] **Qwen3.5 watch → eval**: currency agent already flags it; when the Ollama
    build lands, run eval_models.py A/B same-day. Likely next SMALL_MODEL.
32. [E] **keep_alive tuning**: 30m pin costs 5.3GB VRAM daytime; consider 10m on
    weekdays 9-18h (Claude Desktop contention) via env — trivial experiment.
33. [M] **Speculative decoding re-test on 8b** (not the MoE): a 0.6b draft model
    pairing with qwen3:8b in llama.cpp showed real gains in 2026 tests for DENSE
    models — your llamacpp toolkit is already installed; 30-min experiment.
34. [H] **RAM purchase trigger file**: you said "when prices are manageable" — a
    currency-agent watch on DDR5 2x32GB price via a retailer RSS/API; alert under
    your threshold. Turns "someday" into a trigger.

## 6. Skills & tools to adopt (curated for YOU)

35. [★E] **anthropics/skills repo** + ComposioHQ/awesome-claude-skills: mine for the
    fleet's skill library (skill-miner cron exists — point it at these two repos).
36. [E] **Superpowers plugin** (plan-spec-test workflow) for your Claude Code
    sessions on ai-job-hunter — the discipline layer your solo projects lack.
37. [E] **Context7** for Claude Code: fresh library docs on demand — kills the
    "trained on old Next.js API" class of bug in your projects.
38. [M] **Claude-Mem / persistent memory plugin**: cross-session memory for Claude
    Code work on your repos (Cowork already has memory; Code sessions don't).
39. [M] **Jeff Emanuel's headless browser** (renders JS→Markdown): upgrade
    scout/research agents to read JS-heavy job boards they currently can't.
40. [E] **x-research-skill** (rohunvora): X research via Claude without API — feeds
    your X watchlist digestion (your #1 requested intel source).

## 7. UX / daily experience

41. [★E](B) **Morning brief → phone-first format**: first 3 lines = scoreboard, ONE
    thing, needs count. Everything else below the fold. You read it on a phone;
    format for the lock screen.
42. [E](B) **Dashboard dark-red alert banner** when ANY needs_human is
    income-critical (interview invite, follow-up due) — visual triage.
43. [E](B) **/done command**: "what did the fleet DO today" — one-liner per agent
    action. Builds trust in the invisible 2am work.
44. [M](B) **Weekly review as a conversation**: Sunday review ends with 3 questions
    (reply via Telegram) — answers feed feedback.py. The loop closes only if
    reflection is 2-way.
45. [E](B) **Brief includes gig matches** when score ≥ 5 (gigs.md exists but isn't
    in the brief composition yet — 5-line change).
46. [M] **Open WebUI pin**: pin your 3 real workflows (tailor/prep/code) as WebUI
    presets so desktop use matches Telegram capability.

## 8. Security / resilience next wave

47. [★E] **Rotate ai-job-hunter .secret.key** (owed since 07-06; the app's rotation
    path preserves encrypted rows).
48. [M] **hermes secrets → Bitwarden**: move TELEGRAM_BOT_TOKEN + HEALTHCHECK_URL
    out of plaintext .env (v0.18 supports it).
49. [E](B) **git filter-repo purge** of the old committed .db/.secret.key in
    ai-job-hunter history — before any repo ever flips public.
50. [E](B) **Backup the backup**: Harmony_backup is on the same physical disk as
    Harmony's OneDrive cache. One robocopy target on an external drive (when you
    buy one for Steam — same purchase solves both).
51. [E](B) **Weekly restore-test**: backup that's never been restored is a hope,
    not a backup — monthly cron picks 3 random files, diffs mirror vs source.
52. [M] **Windows-MCP + computer-use hygiene**: the connector reaper now works;
    add windows-mcp.exe python children to the guardian's dup patterns explicitly
    (they were the biggest single RAM eater in the 160).

## 9. Life-OS beyond the job hunt (Harmony's other pillars)

53. [M](B) **Finance: runway auto-calc**: finance agent reads a simple
    balance+burn line you update weekly → brief shows "runway: N weeks" — THE
    number that contextualizes every job-hunt decision.
54. [M](B) **Health streak in scoreboard**: you built streaks for applications;
    mirror it for workout days. Same code, second habit.
55. [E](B) **Learning loop → job skills**: SRS cards exist; auto-generate 2
    cards/week from the tech in jobs you're applying to (interview prep compound
    interest).
56. [M](B) **Bible_App / personal projects rotation**: one "personal project hour"
    block suggested per week by the brief when application target is met — sanity
    is a performance asset.
57. [M] **Relationships tracker**: networking.md tracks professional touches; a
    personal equivalent (family/friends contact cadence) is the same code with a
    different file.

## 10. Project-specific (your repos)

58. [M](B) **ai-job-hunter ↔ fleet merge decision**: you now have TWO job engines
    (career_agent fleet + ai-job-hunter app). Decide the seam: app = discovery/apply
    UI, fleet = tracking/drafting/coaching. Document it in both AGENTS.md files.
59. [E](B) **pokemon-drop uptime check** in currency daily (it's your demo for
    employers — a 404 during an interview is catastrophic and free to prevent).
60. [M](B) **Portfolio: add the fleet itself as a case study** — "I built a 24-agent
    autonomous system with verification loops, self-healing, and $0 marginal cost"
    is your strongest differentiator vs other self-taught candidates. The audit
    docs practically write the case study.
61. [M] **boombox-v5 Supabase advisors**: the Supabase connector here can run
    get_advisors (security/performance lints) — free professional-grade review.
62. [E](B) **AGENTS.md for viral-forge + giveaway-app + boombox** (only 2 repos
    have them; currency agent watches the standard).

## 11. Fresh from X (this sweep — adapted to YOUR fleet, not copied)

63. [★E](B) **"Plan-space" polish loop** (@doodlestein, Jan 2026): before implementing
    anything big, paste the plan into a SECOND model for diff-style critique; repeat
    until suggestions go incremental. Your router already has cloud escalation via
    subscriptions — wire a `/plan` command: local draft → redacted cloud critique →
    local merge. "It's a lot easier to operate in plan space than code space."
64. [★M](B) **"Fresh-eyes until clean" revision loop** (@doodlestein): the overnight
    worker has ONE critic pass; his battle-tested pattern is REPEATED review rounds
    until a pass finds nothing (capped). One-line change to the revision loop cap +
    exit condition — measurably better drafts for free.
65. [M] **Beads-style task graph for the overnight queue** (@doodlestein via Steve
    Yegge's beads): your queue is flat files; add a `deps:` header line so multi-step
    projects (e.g. "research company → tailor resume → draft cover") execute in
    order across nights instead of colliding in one.
66. [M] **Skills as rich directories** (@doodlestein's core thesis): your 9 Hermes
    skills are single markdown files; his "progressive disclosure + agent ergonomics"
    structure (SKILL.md + reference files + scripts) is why his agents outperform.
    Upgrade job-application + voice-match first (income-critical).
67. [E] **Karpathy's workflow shift** (Jan 2026 post, 144k-star guideline repo):
    he's at 80% agent-coding now; his 4 guardrails (no silent assumptions, no
    over-engineering, no orthogonal changes, verify success criteria) → add to the
    fleet's overnight worker + /code preambles verbatim. (= item #26, confirmed
    from the primary source.)
68. [E] **Berman's Loop Library** (26 battle-tested agent loops, free): each has
    explicit verify/stop criteria — mine it for the scout + research agents' missing
    verification gates (explainx.ai/loops has ~100 more with kickoff prompts).
69. [E] **"Don't prematurely automate"** (@doodlestein principle): do a workflow
    manually until you FEEL the core value loop, then automate. Directly relevant:
    log 10 applications by hand in Job_Tracker before building more application
    automation — the outcome-learner needs YOUR intuition encoded, not guesses.
70. [E](B) **Grouped-commit hygiene prompt** (@doodlestein): his exact "commit in
    logically connected groupings with detailed messages" prompt → add to the
    deploy_fleet.ps1 workflow + AGENTS.md files.
71. [M] **Agent-first tooling** (@doodlestein's biggest lesson): "make tooling for
    the AGENT, not for you — the agents are better at using it." Your comms/
    blackboard already follows this; apply it to the next tool you build (e.g.
    outcome data as JSONL the agents query, not just markdown you read).

## Top 5 if you only pick 5
1. #1+#2 Gmail/Todoist bridges (closes the oldest gap, zero keys, I can build now)
2. #7 Auto-tailor pipeline (wake up to drafted applications)
3. #8 Log applications (unblinds outcome-learner + QLoRA + everything)
4. #60 Fleet-as-case-study on the portfolio (converts this work into interviews)
5. #28 Reboot tonight (finishes today's cleanup)

## Sources
- https://www.firecrawl.dev/blog/best-claude-code-skills
- https://designrevision.com/blog/best-claude-code-plugins
- https://composio.dev/content/top-claude-skills
- https://localaimaster.com/blog/build-local-ai-agent
- https://angelo-lima.fr/en/ollama-2026-state-of-the-art-en/
- https://medium.com/@beatwad/how-i-automated-my-linkedin-job-search-using-an-llm-87b892f6ab07
- https://sanalabs.com/agents-blog/ai-agents-for-automating-work-enterprise-guide-2026
- https://www.supercareer.co/blog/run-llms-locally-career-impact

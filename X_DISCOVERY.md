# X (Twitter) Discovery — Brian's #1 discovery source

X is where Brian finds the best new AI tools, projects, and people first. This documents how the fleet pulls that signal in.

## The honest constraint
X removed free API access, and the old free scrapers (Nitter, snscrape) are dead. So **X cannot be scraped silently/unattended for free** the way Hacker News, GitHub Trending, and arXiv can (those run automatically in `currency_agent.py`). X is read **browser-assisted** through Brian's own logged-in session via the Claude-in-Chrome extension, **on demand** — when Brian asks ("scan my X") or when his browser is open during a session.

## What the scan does
Driven by `shared/x_watch.json`. When run, it reads the chosen surfaces and extracts every tool / repo / model release / technique / notable thread, with its link:
1. **Bookmarks** (`x.com/i/bookmarks`) — highest signal: what Brian deliberately saved.
2. **Home / Following feed** — breadth: what his follows are posting right now.
3. **Watched accounts** — the curated proven roster in `x_watch.json` (researchers, practical builders, agent/open-source, solo vibecoders).
4. **Lists** — any X Lists Brian adds.

It then dedupes against `comms/.currency_discovery_seen.json` (shared with the auto-discovery engine so nothing repeats), has the local LLM curate the few genuinely worth his time, and appends them to `comms/currency.md` / the discovery report.

## Finding new proven people (deep cuts)
`discover_new_accounts: true` turns on growth: the scan notes which **not-yet-followed** handles the trusted set keeps amplifying (quotes, replies, recommends), and drops them into `candidate_accounts` for Brian to approve. Approved ones get promoted into `watched_accounts`. Over time the roster compounds from "the obvious greats" toward the deep cuts.

## Seed roster (2026, verify to taste)
- **Researchers / thinkers:** karpathy, ylecun, polynoamial (Noam Brown), svpino, rasbt (Raschka), DAIR_AI
- **Practical builders:** simonw (Simon Willison), leerob (Cursor), mattwolfe, _akhaliq (AK — papers/releases), swyx
- **Agents / open source / labs:** steipete (OpenClaw), NousResearch (the fleet host), ollama, AnthropicAI, claudeai, OpenAI, AIatMeta, GoogleDeepMind, vercel, cursor_ai
- **Solo vibecoders (Brian's lane):** jackfriks, rileybrown, gregisenberg, corbin_braun

## How to run it
- Just say **"scan my X"** (or "what's new on my X") and I'll run the browser-assisted scan on the surfaces in `x_watch.json`, fold the finds into the discovery report, and propose new accounts.
- Or keep your browser open and I can run it as part of a session.
- The automatic, unattended part (HN / GitHub Trending / arXiv) keeps running daily/weekly regardless — X is the human-in-the-loop layer on top.

## Future option (if you ever want unattended X)
The only reliable unattended paths cost money or effort: the paid X API, or a scheduled headless browser using your saved X session (fragile, against ToS to varying degrees). Not worth it now — the on-demand browser scan + your bookmarks habit covers it for free.

---
name: mcp-optimizer
description: Use whenever MCP servers, connectors, tools, or token/context efficiency come up — picking which MCP to use for a task, auditing what's enabled, turning off unused servers to save tokens, finding better/new MCP servers or tools, or a periodic "MCP tune-up." Trigger even if the user doesn't say "MCP" but mentions slow/expensive sessions, context bloat, "too many tools," "which tool should I use," connectors (Gmail/Notion/Figma/etc.), or wanting the setup leaner. This is a recurring maintenance discipline, not a one-off — run it monthly and whenever the toolset changes.
---

# MCP Optimizer

Keep the MCP/tool surface **small, intentional, and current.** Every enabled server is a standing tax (schema tokens, a subprocess, a chance the model picks the wrong tool). The goal is the *fewest* servers that cover the actual work — and a habit of re-checking as the ecosystem moves.

## The three jobs this skill does
1. **Decide** which MCP/tool to use for the task at hand (right tool, not the first tool).
2. **Audit & prune** — turn off what isn't being used in this context.
3. **Discover & adapt** — find better servers/tools and fold in current best practice from the people doing this well.

Always do #3's research step when running an audit — the ecosystem changes monthly. Don't rely on memory; pull current sources (see `references/research-2026.md` for who to read and the latest findings).

## Core principles (2026 best practice — sources in references)
- **Quality over quantity. Keep ~5–6 servers active per context.** Each spawns a subprocess and adds schema tokens; too many and the model slows and mis-picks. ([builder.io], [thenewstack])
- **Context-scope the loadout.** A *coding* session needs a different set than a *life-ops* chat. Don't run Gmail/Calendar/Spotify in a Claude Code build session; don't run Supabase/Playwright in a Claude Desktop life chat.
- **Search-first is already on in Claude Code** — Tool Search auto-activates when tool schemas exceed ~10% of context (the "deferred tools" you see). So the win isn't eager-vs-lazy; it's **fewer servers** (smaller name list, less mis-trigger, fewer processes) + **disabling dead/unauth connectors**.
- **Dead weight is the easy win.** Any server showing "needs authentication" / not connected is pure noise — remove it.
- **Prefer one good server over three overlapping ones.** Don't run a legacy server *and* its plugin replacement (e.g. `puppeteer` + Playwright, `postgres` + Supabase).
- **Response/field filtering & code-execution patterns** beat raw tool-wrapping for token cost — prefer servers built for agents, not thin API wrappers. ([anthropic code-execution], [speakeasy])

## Decide: which tool for the task
Pick by job, and reach for the leanest thing that does it:
| Task | Use |
|---|---|
| Library/framework docs, version-correct APIs | **context7** (always — beats guessing from memory) |
| Repo ops (PRs, issues, code search, releases) | **github** |
| Browser drive / E2E / screenshots / visual check | **playwright** |
| Design → code, reading a Figma file | **figma** |
| DB schema/migrations/queries (Supabase projects) | **supabase** |
| Deploy/preview/logs (Vercel projects only) | **vercel** |
| Web research / current info | **WebSearch** (built-in) or a search MCP |
| Life-ops (mail, calendar, tasks, notes) | claude.ai connectors — **Claude Desktop only**, not Code |

If two tools overlap, prefer the built-in (WebSearch, Read/Grep/Glob) over an MCP, and the maintained plugin over a legacy standalone server.

## Audit & prune (the routine)
1. **List reality:** `claude mcp list` (shows connection status). Note every server + whether it's Connected / Needs-auth.
2. **Classify** each against the *current context* using `references/current-loadout.md` (Brian's keep/disable decisions). Buckets: **keep** (used in this context), **on-demand** (enable only when that work starts), **disable** (unused here), **remove** (dead/needs-auth/legacy-redundant).
3. **Apply what's safely controllable:**
   - **Plugins** (dev MCPs) → toggle in `~/.claude/settings.json` `enabledPlugins` (`true`/`false`). Reversible. Back the file up first.
   - **Legacy root servers** in `~/.claude.json` `mcpServers` → `claude mcp remove <name>` (don't hand-edit the big state file).
   - **claude.ai connectors** → these are account-level and **shared with Claude Desktop**, so confirm before disconnecting. Disable via `/mcp` in Claude Code or claude.ai → Settings → Connectors. Never silently disconnect a connector the user relies on elsewhere.
4. **Verify:** re-run `claude mcp list`; confirm the kept set connects and nothing needed broke.
5. **Record:** update `references/current-loadout.md` with the date + what changed and why (this is the memory that makes next month's audit fast).

Safety: back up `settings.json` before editing; never disconnect a shared/outward connector without the user's OK; prune dead-auth servers freely.

## Discover & adapt (don't stagnate)
When auditing, also scout for better tools:
- **Pull current best practice + new servers** — read the sources in `references/research-2026.md` and refresh them (they go stale). Note who's worth following.
- **Evaluate a candidate server** before adopting: Does it cover a real gap? Is it agent-built (filtered responses, sane tool count) or a thin API wrapper? Maintained/official? **Security:** what scopes/data does it touch — an MCP can exfiltrate or take destructive actions, so vet permissions and prefer official/audited servers.
- **Adopt only if it replaces something or fills a real gap** — and when you add one, remove one (keep the ~5–6 budget).
- **Anti-pattern:** installing servers "just in case." Every idle server is a standing cost.

## Cadence
- Run a full audit **monthly** (or when sessions feel slow / after adding tools).
- Keep `references/current-loadout.md` as the living record; keep `references/research-2026.md` refreshed with the latest findings + sources.

See `references/current-loadout.md` for the current keep/disable plan and `references/research-2026.md` for findings, recommended servers, and who to follow.

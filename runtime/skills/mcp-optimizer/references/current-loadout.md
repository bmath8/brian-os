# Current MCP Loadout — keep / disable decisions
_Living record. Last audit: 2026-06-20. Re-audit monthly. Source of truth for what SHOULD be enabled; reconcile against `claude mcp list`._

## Snapshot 2026-06-20 — ~25 servers active (research says aim for ~5–6 per context)

### Plugin MCP servers (dev work — toggle in `~/.claude/settings.json` → `enabledPlugins`)
| Server | Decision | Why |
|---|---|---|
| context7 | **KEEP** | Version-correct library docs — highest-value dev MCP |
| github | **KEEP** | Repo ops across all projects |
| playwright | **KEEP** | Browser/E2E/screenshots (boombox, giveaway, portfolio UI) |
| figma | **KEEP** | Design→code (active design work) |
| supabase | **KEEP** | DB for projects that use it |
| vercel | **ON-DEMAND** | Only if a project deploys to Vercel (job-hunter=Render, others=Docker). Enable when needed. |
| linear | **DISABLE** | Not used — Brian tracks work in Todoist + Obsidian + FOR TOM.md, not Linear |
| typescript-lsp / pyright-lsp | **KEEP** | Real code intelligence for TS (boombox/giveaway) + Python (fleet/job-hunter) |
| serena | already off | — |

### claude.ai connectors (account-level; shared with Claude Desktop — confirm before disconnecting)
**Rule: NONE of these belong in a Claude Code build session.** They're life-ops, used in Claude Desktop chat.
| Connector | Claude Code | Claude Desktop (life-ops) |
|---|---|---|
| Gmail, Google Calendar, Google Drive | DISABLE | KEEP (brief/calendar life-ops) |
| Todoist | DISABLE | KEEP (task system) |
| Notion | DISABLE | KEEP if used for notes |
| Indeed | ON-DEMAND | ON-DEMAND (job hunt) |
| Canva, HyperFrames/HeyGen | ON-DEMAND | ON-DEMAND (content creation) |
| Spotify | DISABLE | OPTIONAL (not productivity) |
| monday.com, Asana | **REMOVE** | **REMOVE** — Brian uses Todoist, not these |
| Manufact, Docusign, Postman, Slack, Microsoft 365, Zapier, Asana(2) | **REMOVE** | **REMOVE** — all "needs authentication" = dead weight, never used |

### Legacy servers scoped to the `C:\Users\mathe` dir in `~/.claude.json`
`filesystem, github, brave-search, sqlite, postgres, puppeteer` — **dormant cruft** (didn't appear in `claude mcp list`; only load when Claude Code runs from `C:\Users\mathe`). Superseded: github→github plugin, puppeteer→playwright, postgres→supabase, filesystem→built-in Read/Grep/Glob, sqlite→unused, brave-search→built-in WebSearch.
**To remove cleanly:** `cd C:\Users\mathe` then `claude mcp remove <name>` for each (they're in that project's *local* scope, so the remove must run from that dir). Harmless if left, but tidy to clear. Don't hand-edit `~/.claude.json` (52 KB state file).

## Target steady state
- **Claude Code (build):** context7, github, playwright, figma, supabase, + LSPs. Vercel on-demand. = ~5 MCP + 2 LSP. ✅ in budget.
- **Claude Desktop (life-ops):** Gmail, Calendar, Drive, Todoist, (Notion). = ~5. ✅ in budget.
- **Everything else:** disabled or removed; enable on-demand for the specific task, then turn back off.

## Change log
- **2026-06-20:** Initial audit. Disabled `linear` plugin (committed). Recommended: remove monday/Asana + all needs-auth connectors; remove legacy root servers; scope connectors to Desktop-only. (Connector changes left to Brian — account-level, shared with Desktop.)

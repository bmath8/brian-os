# MCP Optimization — Research & Sources
_Refresh this when you run an audit; the ecosystem moves monthly. Last refreshed 2026-06-20._

## Current best-practice findings (2026)
- **Keep ~5–6 servers active per context.** Each spawns a subprocess; too many slows the agent and causes wrong-tool picks. (builder.io, The New Stack)
- **Search-first tool discovery is the #1 lever** — don't inject 50 schemas at start; expose one `search_tools()` and load on demand. Cuts schema tokens 80–95%. **Claude Code does this automatically** (Tool Search activates when tool descriptions exceed ~10% of context — that's the "deferred tools" list). So for Claude Code the remaining levers are *fewer servers* + *pruning dead/auth-failing ones*. (MindStudio, Speakeasy)
- **Code-execution pattern**: present MCP servers as code APIs the agent calls in code, loading only needed tools and filtering data before returning — large token savings for data-heavy work. (Anthropic Engineering: "Code execution with MCP")
- **Consolidated dispatcher pattern**: one tool with an `action` arg beats 80 one-per-endpoint tools (~10,000 tokens → ~100). Prefer servers designed this way. (StackOne)
- **Response/field filtering**: request only needed fields; avoid servers that dump full API payloads. (StackOne, MindStudio)
- **Tool quality > quantity**: most MCP servers are thin API wrappers not built for agents; prefer intentional, agent-built tools. (Anthropic)
- **Security is part of optimization**: an MCP can read/exfiltrate data and take destructive actions. Vet scopes; prefer official/audited servers; remove anything unauthenticated/unused. (shareuhack security ranking)

## Recommended servers by job (2026 consensus)
- **Backend/dev core:** GitHub + Context7 (covers most). 
- **Frontend:** + Figma + Playwright.
- **Research:** + a search MCP (Brave/Perplexity) or built-in WebSearch.
- **DB:** Supabase / Postgres (one, not both).
- Consensus starter set: Filesystem (or built-in) + GitHub, then Playwright + Context7 + Figma. (builder.io, firecrawl, developersdigest, obot.ai, taskade)

## Candidate servers worth evaluating (gaps Brian might fill)
- **Serena** (already installed, disabled) — semantic code retrieval/LSP-like; re-evaluate for large-repo work vs the LSP plugins.
- **Brave Search / Perplexity MCP** — independent web index; only if built-in WebSearch proves insufficient.
- **Sequential-thinking / memory MCPs** — usually redundant with Claude's own reasoning + the fleet's RAG; skip unless a concrete gap.
- Evaluate any candidate on: real gap? agent-built (filtered, few tools)? maintained/official? safe scopes? If yes and it replaces something, adopt and drop one.

## People / sources to follow (refresh the list as the field changes)
- **Anthropic Engineering blog** — canonical on MCP + code-execution + tool-search (anthropic.com/engineering).
- **Claude Code docs** (code.claude.com/docs) — tool search, MCP config, plugins.
- Practitioner write-ups that have been consistently good: Builder.io blog (best-servers roundups), The New Stack, Speakeasy, StackOne, MindStudio (token-optimization deep dives), firecrawl/developersdigest (curated server lists).
- Watch the official MCP registry / awesome-mcp lists for new, maintained servers.

## Sources (2026-06-20 pull)
- https://thenewstack.io/how-to-reduce-mcp-token-bloat/
- https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2
- https://www.mindstudio.ai/blog/optimize-mcp-server-token-usage
- https://www.anthropic.com/engineering/code-execution-with-mcp
- https://www.stackone.com/blog/mcp-token-optimization/
- https://www.builder.io/blog/best-mcp-servers-2026
- https://www.shareuhack.com/en/posts/best-mcp-servers-guide-2026
- https://www.developersdigest.tech/best/mcp-servers

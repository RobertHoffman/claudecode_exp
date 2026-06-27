---
name: web-search
description: >
  Web search via Brave Search API (L4 fallback). Use this skill when you need to find
  information on the web but WebSearch tool is unavailable or returning errors.
  Triggers when user says "search the web", "google X", "find docs for Y", or when
  WebSearch returns 400/2013 (MiniMax M3 gateway error) or L2 mcp__brave-search__* is
  not visible in the tool list (Claude Code settings.json MCP silent ignore bug).
---

# Web Search Helper (L4 Fallback)

When web information is needed and the standard `WebSearch` tool or `mcp__brave-search__*` MCP server is unavailable, use the global `web_search` command. This bypasses Claude Code's MCP loading layer entirely by calling the Brave Search API directly via curl.

## Quick Start

```bash
# Default: 5 results
web_search "Claude Code MCP docs"

# Custom count
web_search "qmd 查询优化" 3
```

## 4-Layer Fallback Priority

| Priority | Path | Status | When to use |
|----------|------|--------|-------------|
| **L1** | `WebSearch` tool (via MiniMax M3) | ⚠️ May return 400 2013 | Try first; gateway error → fall through |
| **L2** | `mcp__brave-search__*` MCP | ❌ Not visible in most sessions | Claude Code settings.json mcpServers silent ignore bug (GitHub #646) |
| **L3** | `WebFetch` (URL known) | ✅ Always works | When you have the exact URL (GitHub, official docs, etc.) |
| **L4** | `web_search "kw"` global command | ✅ **Always works** | When L1 fails AND L2 not visible AND no known URL |

## Why L4 Exists

1. **L1 unreliable**: MiniMax M3 gateway frequently returns `400 invalid params, function name or empty (2013)` — server-side bug, no Driver-side fix
2. **L2 silently ignored**: Claude Code `settings.json` `mcpServers` configs are silently ignored (verified 2026-06-26 with PID 4046 — 4 MCPs all invisible)
3. **L3 needs URL**: WebFetch requires knowing the exact URL, not useful for discovery
4. **L4 = curl + Brave API**: Bypasses all Claude Code MCP layers; works in any session that can run bash

## Implementation Details

- **Script**: `~/.claude/scripts/web_search.sh`
- **PATH symlink**: `~/.local/bin/web_search` → script (auto-installed)
- **API key source**: `BRAVE_API_KEY` env var OR `~/.bashrc` `export <BRAVE_API_KEY>`
- **Encoding**: Python `urllib.parse.quote()` for URL-safe query
- **Output format**: Structured `1. Title / URL / snippet` blocks (Chinese + English supported)
- **Exit codes**: 0=OK, 1=no arg, 2=key missing, 3=curl fail, 4=JSON parse fail

## Verification (2026-06-26)

```bash
$ web_search "Claude Code MCP" 2
1. Connect Claude Code to tools via MCP - Claude Code Docs
   https://code.claude.com/docs/en/mcp
2. GitHub - steipete/claude-code-mcp: ...
```

Returns real results in ~2s, fully parseable, no Claude Code dependency.
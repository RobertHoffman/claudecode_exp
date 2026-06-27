---
name: session-to-qmd
description: Ingest Claude Code session JSONL files into QMD-indexed daily-logs. Parses ~/.claude/projects/-*/<session>.jsonl, extracts user/assistant messages (drops thinking + tool noise), writes markdown to ~/.claude/knowledge/daily-logs/ for long-term semantic search via QMD.
---

# session-to-qmd

Auto-ingest Claude Code session history into QMD for cross-session semantic search.

## What it does

1. **Parses** all `*.jsonl` files under `~/.claude/projects/-*/`
2. **Extracts** user messages + assistant text responses (drops `<thinking>` blocks, `tool_use` snippets, `tool_result` content)
3. **Writes** markdown to `~/.claude/knowledge/daily-logs/YYYY-MM-DD-<session-id>-<hash>.md`
4. **Deduplicates** by content hash — re-running is idempotent
5. **Re-embeds** the `daily-logs` collection so QMD BM25/vector search picks it up

## When to use

- **Manual**: run `python3 /home/rucli/.claude/skills/session-to-qmd/scripts/ingest.py` to ingest immediately
- **Manual embed (recommended)**: `qmd-safe embed -c daily-logs` — uses wrapper with CPUQuota=50% + taskset -c 0,1 so it does NOT starve the Claude Code session
- **Cron**: 23:30 daily (see `ingest-cron.sh` — registers via `crontab -e`; cron already calls qmd-safe internally)
- **QMD auto**: `qmd update` will trigger the `update:` field in `index.yml` for `daily-logs`

## Files

- `scripts/ingest.py` — JSONL → markdown parser (idempotent, dedupe by hash)
- `scripts/ingest-cron.sh` — daily runner (ingest + qmd-safe embed + qmd-safe update)
- `README.md` — full design doc

## Performance / CPU safety (2026-06-26)

**Always invoke qmd via the `qmd-safe` wrapper** (`/home/rucli/.local/bin/qmd-safe`).
It applies `systemd-run --user --scope -p CPUQuota=50%` + `taskset -c 0,1` for CPU-heavy
subcommands (`embed`, `update`, `query`, `vsearch`). Search/get/ls/status/mcp bypass
the wrapper since they don't load the embedding model.

| Subcommand | Wrapper path | CPU bound? |
|---|---|---|
| `search`, `get`, `multi-get`, `ls`, `status`, `collection`, `context`, `cleanup`, `mcp` | passthrough | no |
| `embed`, `update`, `query`, `vsearch` | systemd-run + taskset | yes (50%) |

Background: bare `qmd embed` loads 300MB embeddinggemma-300M and saturates all 4 cores,
blocking the Claude Code session (verified 2026-06-26: node-llama-cpp worker capped at
exactly 50.0% CPU with affinity mask `3` = cores 0,1).

## Secrets safety

- **Strips `tool_result` content** (may contain API keys, tokens, raw user data)
- **Truncates** at 8000 chars per message to keep md files lean
- **No external network** — only reads local JSONL, writes local markdown
- **No API keys** in code

## QMD integration

The `daily-logs` collection in `~/.config/qmd/index.yml` has:

```yaml
daily-logs:
  path: /home/rucli/.claude/knowledge/daily-logs
  pattern: "**/*.md"
  update: "bash /home/rucli/.claude/skills/session-to-qmd/scripts/ingest-cron.sh"
```

So `qmd update` will run the cron script automatically as part of its collection update flow.

## Search examples

```bash
# Find sessions about a specific topic
qmd search "CUDA embed" -c daily-logs -n 5

# Find yesterday's decisions
qmd search "决定|decision" -c daily-logs -n 5

# Hybrid search across all collections
qmd query "subagent delegation rules" -c daily-logs,claude-memories
```

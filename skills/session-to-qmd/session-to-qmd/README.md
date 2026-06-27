# session-to-qmd

Auto-ingest Claude Code session history into QMD for long-term semantic search.

## Problem

Claude Code writes each session to `~/.claude/projects/-*/<session-id>.jsonl`.
These files are huge (100MB+), full of tool noise, thinking blocks, and tool results.
Driver/Worker sessions want to recall past context ("did I see this error before?"),
but reading raw JSONL is impractical.

## Solution

Parse each session into a clean markdown transcript, write to QMD-monitored dir,
re-embed for vector search.

## Design choices

| Decision | Why |
|---|---|
| One md per session per day | Date prefix → natural temporal grouping |
| Filename = `YYYY-MM-DD-<session>-<hash>.md` | Hash = content fingerprint, dedup by mtime |
| Drop `<thinking>` blocks | Internal noise, not user-facing knowledge |
| Drop `tool_result` content | May contain secrets, user PII |
| Keep `tool_use` snippets (truncated 200 chars) | Helpful for "what did I run?" recall |
| Truncate messages at 8000 chars | Some single messages can be 100KB+ |
| Cap at 500 messages per session | Safety net for runaway sessions |
| Skip sessions < 100 bytes | Empty/test sessions |

## Usage

### Manual one-shot

```bash
python3 /home/rucli/.claude/skills/session-to-qmd/scripts/ingest.py
```

Output: prints per-file status, summary at end.

### Manual embed (CPU-safe)

```bash
# Recommended — wrapper enforces CPUQuota=50% + taskset -c 0,1
qmd-safe embed -c daily-logs

# Avoid direct qmd embed — saturates all 4 cores and blocks Claude Code
```

### Cron (daily 23:30)

```cron
30 23 * * * bash /home/rucli/.claude/skills/session-to-qmd/scripts/ingest-cron.sh
```

Logs to `~/.claude/logs/session-to-qmd.log`. The cron script uses `qmd-safe` internally.

### Auto-trigger via QMD

`~/.config/qmd/index.yml` has:

```yaml
daily-logs:
  path: /home/rucli/.claude/knowledge/daily-logs
  pattern: "**/*.md"
  update: "bash /home/rucli/.claude/skills/session-to-qmd/scripts/ingest-cron.sh"
```

So `qmd update` will trigger the cron script for daily-logs automatically.

## Search

```bash
# Sessions about specific topic
qmd search "qmd CUDA" -c daily-logs -n 5

# Find decisions
qmd search "决定" -c daily-logs -n 5

# Hybrid: across memory + daily logs
qmd query "agent delegation failure" -c daily-logs,claude-memories
```

## Maintenance

- **First run**: parses ALL sessions — may take 30s+ for 10 sessions
- **Subsequent runs**: only writes when content hash changes
- **Cleanup**: md files self-clean (re-runs delete old hashes for same session id)

## Files

- `SKILL.md` — Claude Code skill definition
- `scripts/ingest.py` — JSONL → markdown parser
- `scripts/ingest-cron.sh` — daily cron runner (ingest + qmd-safe embed/update)
- `README.md` — this file

## Performance / CPU safety

The cron script and any manual `qmd embed` calls go through `~/.local/bin/qmd-safe`,
which wraps CPU-heavy subcommands (`embed`/`update`/`query`/`vsearch`) in
`systemd-run --user --scope -p CPUQuota=50%` + `taskset -c 0,1`.

Verified 2026-06-26: node-llama-cpp worker stayed at exactly 50.0% CPU with affinity
mask `3` (cores 0,1) during a full `embed -c daily-logs` run. Bare `qmd embed` would
otherwise saturate all 4 cores and freeze the Claude Code session.

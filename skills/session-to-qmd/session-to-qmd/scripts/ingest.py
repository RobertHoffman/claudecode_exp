#!/usr/bin/env python3
"""
session-to-qmd ingest.py

Parse Claude Code session JSONL files and convert to QMD-indexable markdown.

Pipeline:
  ~/.claude/projects/-*/<session-id>.jsonl
    -> extract user messages + assistant text responses
    -> write ~/.claude/knowledge/daily-logs/YYYY-MM-DD-<session>-<hash>.md
    -> QMD BM25/vector search ready

Design choices:
  - Only text content (drop thinking + tool_use/tool_result noise)
  - Dedupe by content hash (avoid re-indexing identical sessions)
  - One markdown per session per day (date = first message timestamp)
  - Skip synthetic/empty sessions
  - Secrets-safe: never include tool result content that may contain API keys
  - File path encoding: session id is uuid, hash is sha256(content)[:8]
"""
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Tuple

PROJECTS_DIR = Path("/home/rucli/.claude/projects")
OUTPUT_DIR = Path("/home/rucli/.claude/knowledge/daily-logs")
MAX_MESSAGES = 500        # safety cap per session
MAX_CONTENT_CHARS = 8000  # truncate per-message to keep md sane

# Only ingest sessions from the primary project dir (-home-rucli).
# Other dirs are WSL /mnt/ Windows paths, sub-projects, or temp scratch.
INCLUDE_PROJECT_PATTERNS = ("-home-rucli",)


def iter_jsonl_files() -> Iterator[Path]:
    """Yield all session JSONL files under projects dir, filtered."""
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        name = project_dir.name
        if not any(p in name for p in INCLUDE_PROJECT_PATTERNS):
            continue
        for jsonl in project_dir.glob("*.jsonl"):
            yield jsonl


def extract_messages(jsonl_path: Path) -> Tuple[Optional[str], list]:
    """
    Parse a JSONL session file, return (date_str, [(role, text), ...]).

    date_str = YYYY-MM-DD of first user message
    messages = list of (role, text) — role in {user, assistant}
    """
    user_messages: list = []
    assistant_messages: list = []
    first_user_ts: Optional[str] = None

    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Standard Claude Code message format
                msg_type = obj.get("type", "")
                if msg_type not in ("user", "assistant"):
                    continue
                msg = obj.get("message", {})
                content = msg.get("content", "")
                ts = obj.get("timestamp", "")

                # Extract text from content (list or str)
                texts: list = []
                if isinstance(content, str):
                    texts.append(content)
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            if block.get("type") == "text":
                                t = block.get("text", "")
                                # Filter out thinking blocks (Claude extended thinking)
                                if t and not t.startswith("<thinking>") and "</thinking>" not in t[:200]:
                                    texts.append(t)
                            elif block.get("type") == "tool_use":
                                # Brief: just tool name + short input
                                name = block.get("name", "tool")
                                inp = block.get("input", {})
                                snippet = str(inp)[:200]
                                texts.append(f"[tool_use: {name}] {snippet}")
                            # Skip tool_result blocks (may contain secrets/garbage)

                if not texts:
                    continue

                combined = "\n".join(texts).strip()
                if not combined:
                    continue

                if msg_type == "user":
                    if first_user_ts is None:
                        first_user_ts = ts
                    user_messages.append(combined)
                else:
                    assistant_messages.append(combined)

    except (OSError, UnicodeDecodeError) as e:
        print(f"WARN: cannot read {jsonl_path}: {e}", file=sys.stderr)
        return None, []

    if not user_messages:
        return None, []

    # Pair them up (best-effort: just list sequentially)
    paired: list = []
    for u, a in zip(user_messages, assistant_messages):
        paired.append(("user", u))
        paired.append(("assistant", a))
    # Tail if odd
    if len(user_messages) > len(assistant_messages):
        paired.append(("user", user_messages[-1]))

    # Truncate
    paired = paired[:MAX_MESSAGES]

    # Parse date
    date_str = "unknown"
    if first_user_ts:
        try:
            # Typical format: 2026-06-25T15:30:00.000Z
            dt = datetime.fromisoformat(first_user_ts.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            pass

    return date_str, paired


def render_markdown(session_id: str, date_str: str, messages: list, jsonl_path: Path) -> str:
    """Render messages as markdown."""
    lines: list = []
    lines.append(f"# Session {session_id}")
    lines.append("")
    lines.append(f"- Date: {date_str}")
    lines.append(f"- Source: `{jsonl_path.relative_to(Path.home())}`")
    lines.append(f"- Message pairs: {len(messages) // 2}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for role, text in messages:
        # Truncate long content
        if len(text) > MAX_CONTENT_CHARS:
            text = text[:MAX_CONTENT_CHARS] + "\n\n[... truncated ...]"
        # Clean up excessive whitespace
        text = text.strip()
        if role == "user":
            lines.append("## User")
            lines.append("")
            lines.append(text)
        else:
            lines.append("## Assistant")
            lines.append("")
            lines.append(text)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def content_hash(messages: list) -> str:
    """sha256 of concatenated message text — for dedup."""
    h = hashlib.sha256()
    for _, text in messages:
        h.update(text.encode("utf-8", errors="ignore"))
    return h.hexdigest()[:12]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sessions_processed = 0
    sessions_skipped = 0
    files_written = 0
    files_unchanged = 0

    for jsonl in iter_jsonl_files():
        session_id = jsonl.stem
        # Skip if too small (likely empty)
        if jsonl.stat().st_size < 100:
            sessions_skipped += 1
            continue

        date_str, messages = extract_messages(jsonl)
        if not date_str or not messages:
            sessions_skipped += 1
            continue

        sessions_processed += 1

        h = content_hash(messages)
        out_name = f"{date_str}-{session_id}-{h}.md"
        out_path = OUTPUT_DIR / out_name

        # Skip if already up-to-date (same hash)
        if out_path.exists():
            files_unchanged += 1
            continue

        # Check if any file with same session_id exists (re-index, different hash)
        old_files = list(OUTPUT_DIR.glob(f"*-{session_id}-*.md"))
        for old in old_files:
            try:
                old.unlink()
            except OSError:
                pass

        md = render_markdown(session_id, date_str, messages, jsonl)
        out_path.write_text(md, encoding="utf-8")
        files_written += 1
        print(f"  WROTE: {out_name}  ({len(md)} bytes, {len(messages)} msgs)")

    print()
    print("Summary:")
    print(f"  sessions processed: {sessions_processed}")
    print(f"  sessions skipped:   {sessions_skipped}")
    print(f"  files written:      {files_written}")
    print(f"  files unchanged:    {files_unchanged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

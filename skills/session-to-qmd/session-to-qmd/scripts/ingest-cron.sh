#!/bin/bash
# session-to-qmd cron job
# Runs daily: ingest session JSONL -> markdown -> qmd embed
# Schedule: 23:30 daily (recommended)

set -euo pipefail

LOG_DIR="/home/rucli/.claude/logs"
LOG_FILE="$LOG_DIR/session-to-qmd.log"
INGEST="/home/rucli/.claude/skills/session-to-qmd/scripts/ingest.py"
# Use qmd-safe wrapper to enforce CPUQuota=50% + taskset -c 0,1
# (systemd-run --user --scope -p CPUQuota=50% prevents embed from starving Claude Code session)
QMD="/home/rucli/.local/bin/qmd-safe"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

log "=== session-to-qmd cron start ==="

# 1. Run ingest: parse JSONL -> markdown
log "Step 1: ingest.py"
if ! python3 "$INGEST" 2>&1 | tee -a "$LOG_FILE"; then
    log "ERROR: ingest.py failed"
    exit 1
fi

# 2. Re-embed daily-logs collection (vector refresh)
log "Step 2: qmd embed -c daily-logs"
if ! "$QMD" embed -c daily-logs 2>&1 | tee -a "$LOG_FILE"; then
    log "ERROR: qmd embed failed"
    exit 2
fi

# 3. Run qmd update on daily-logs (file scan)
log "Step 3: qmd embed -c daily-logs"
if ! "$QMD" embed -c daily-logs 2>&1 | tee -a "$LOG_FILE"; then
    log "WARN: qmd embed failed (non-fatal)"
fi

log "=== session-to-qmd cron done ==="

#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run_overnight.sh — Launch ingest_priority.py detached from the terminal.
#
# The process will keep running after you close your SSH session.
# Check progress at any time with:
#   tail -f ../logs/ingest_priority.log
#
# To stop it gracefully (finishes the current subreddit then exits):
#   kill <PID>          # PID is printed when you run this script
#   cat backend/ingest_overnight.pid
#
# Usage:
#   bash run_overnight.sh                       # 500 posts/sub, loop mode
#   bash run_overnight.sh --posts-per-sub 1000  # bigger batches
#   bash run_overnight.sh --dry-run             # test without any writes
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"
PID_FILE="$SCRIPT_DIR/ingest_overnight.pid"
VENV="$SCRIPT_DIR/venv/bin/python3"
COMBINED_LOG="$LOG_DIR/ingest_priority.log"

mkdir -p "$LOG_DIR"

# Check for an already-running instance
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "⚠  An ingestion process is already running (PID $OLD_PID)."
        echo "   tail -f $COMBINED_LOG"
        echo "   Kill it with: kill $OLD_PID"
        exit 1
    else
        echo "Stale PID file found (PID $OLD_PID no longer running) — removing."
        rm -f "$PID_FILE"
    fi
fi

# Activate venv python if available, otherwise fall back to system python3
if [[ -x "$VENV" ]]; then
    PYTHON="$VENV"
else
    PYTHON="python3"
fi

echo "Starting overnight ingestion..."
echo "  Script : $SCRIPT_DIR/ingest_priority.py"
echo "  Log    : $COMBINED_LOG"
echo "  Extra args: $*"
echo ""

# Launch detached — survives SSH disconnect
nohup "$PYTHON" "$SCRIPT_DIR/ingest_priority.py" \
    --loop \
    "$@" \
    >> "$COMBINED_LOG" 2>&1 &

PID=$!
disown "$PID"
echo "$PID" > "$PID_FILE"

echo "✓  Running as PID $PID (saved to $PID_FILE)"
echo ""
echo "Watch progress:"
echo "  tail -f $COMBINED_LOG"
echo ""
echo "Stop gracefully:"
echo "  kill $PID"

#!/usr/bin/env bash
# Runs ingest.py (import stage only) for every subreddit that has both
# a _submissions.zst and _comments.zst in the source directory.
# Usage: bash ingest_batch.sh [--mode import|embed|all] [--limit N]
#
# Defaults to --mode import (no OpenAI calls). Change to --mode all when ready to embed.

set -euo pipefail

ZST_DIR="/home/ubuntu/Nybblers/zst/reddit/subreddits25"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="${MODE:-import}"
EXTRA_ARGS=("$@")   # pass any extra flags through, e.g. --limit 5000

SUBS=(
    Entrepreneur
    SaaS
    startups
    smallbusiness
    digitalnomad
    indiehackers
    freelance
    freelanceWriters
    webdev
    graphic_design
    forhire
    personalfinance
    investing
    financialindependence
    Fire
    stocks
    wallstreetbets
    productivity
    nocode
    Notion
    lifehacks
    getdisciplined
    remotework
    cscareerquestions
    jobs
    careerguidance
    managers
)

LOG_DIR="$SCRIPT_DIR/../logs"
mkdir -p "$LOG_DIR"

ok=0
skipped=0
failed=0

for sub in "${SUBS[@]}"; do
    submissions="$ZST_DIR/${sub}_submissions.zst"
    comments="$ZST_DIR/${sub}_comments.zst"

    args=()
    [[ -f "$submissions" ]] && args+=(--submissions "$submissions")
    [[ -f "$comments"    ]] && args+=(--comments    "$comments")

    if [[ ${#args[@]} -eq 0 ]]; then
        echo "⚠  SKIP  r/$sub — no files found"
        skipped=$((skipped + 1))
        continue
    fi

    echo ""
    echo "════════════════════════════════════════"
    echo "▶  r/$sub"
    echo "════════════════════════════════════════"

    log="$LOG_DIR/${sub}.log"
    if python3 "$SCRIPT_DIR/ingest.py" \
        "${args[@]}" \
        --mode "$MODE" \
        "${EXTRA_ARGS[@]}" \
        2>&1 | tee "$log"; then
        echo "✓  r/$sub done"
        ok=$((ok + 1))
    else
        echo "✗  r/$sub FAILED — see $log"
        failed=$((failed + 1))
    fi
done

echo ""
echo "════════════════════════════════════════"
echo "Batch complete: $ok ok  |  $skipped skipped  |  $failed failed"
echo "════════════════════════════════════════"

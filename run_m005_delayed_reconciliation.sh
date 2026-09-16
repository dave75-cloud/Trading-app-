#!/bin/bash
set -euo pipefail

export PATH="/usr/local/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

PROJECT="$HOME/Projects/Trading-app-"
RUN="$PROJECT/data/research_runs/M005_FORWARD_SHADOW_20260804T120245Z"
OUTPUT_DIR="$RUN/provider_acceptance_v1_2h"
LOG_DIR="$OUTPUT_DIR/logs"
LOCK_DIR="$OUTPUT_DIR/.reconciliation.lock"
POLYGON_AUDIT="$RUN/raw/polygon_reconciliation_only"

mkdir -p "$LOG_DIR" "$OUTPUT_DIR" "$POLYGON_AUDIT"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Another v1.2h reconciliation appears to be running."
  exit 1
fi

cleanup() { rm -rf "$LOCK_DIR"; }
trap cleanup EXIT INT TERM

CYCLE_ID=$(date -u +"%Y%m%dT%H%M%SZ")
LOG="$LOG_DIR/reconciliation_${CYCLE_ID}.log"
exec > >(tee -a "$LOG") 2>&1

cd "$PROJECT"

echo "========================================================================"
echo "KQTRL M005 v1.2h.2 — UPDATER-ONLY DELAYED RECONCILIATION"
echo "========================================================================"
echo "Cycle: $CYCLE_ID"
echo "Canonical M005 signal/state processing: DISABLED"
echo

if [ -z "${POLYGON_API_KEY:-}" ] && [ -f "$HOME/.kqtrl/m005_secrets.sh" ]; then
  source "$HOME/.kqtrl/m005_secrets.sh"
fi

if [ -z "${POLYGON_API_KEY:-}" ]; then
  echo "ERROR: POLYGON_API_KEY is not set."
  exit 1
fi

echo "[1/2] Updating Polygon bars ONLY"
PYTHONPATH=. python3 cli/update_m005_polygon_bars.py \
  --output-dir ./data/live_5m \
  --audit-dir "$POLYGON_AUDIT" \
  --bootstrap-hours 72 \
  --sleep-seconds 0.25

echo
echo "[2/2] Appending complete delayed sessions to acceptance ledger"
PYTHONPATH=. python3 cli/build_m005_provider_acceptance_ledger.py \
  --twelve-dir ./data/live_5m_twelve \
  --polygon-dir ./data/live_5m \
  --output-dir "$OUTPUT_DIR" \
  --price-tolerance-bps 5 \
  --max-sessions-per-run 10

echo
echo "v1.2h.2 reconciliation completed."
echo "Canonical M005 signals/state were NOT processed."
echo "Log: $LOG"

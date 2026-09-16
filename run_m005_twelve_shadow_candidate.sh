#!/bin/bash
set -euo pipefail

cd "$HOME/Projects/Trading-app-"

CANONICAL_RUN="./data/research_runs/M005_FORWARD_SHADOW_20260804T120245Z"
TWELVE_BARS="./data/live_5m_twelve"
CANDIDATE_DIR="$CANONICAL_RUN/provider_candidates/twelve_data_v1_2f"
MAX_STALENESS_MINUTES="${M005_TWELVE_MAX_STALENESS_MINUTES:-20}"

UPDATER="cli/update_m005_twelve_data_bars.py"
GATE="cli/check_m005_live_bar_gate.py"
OBSERVER="cli/run_m005_twelve_shadow_observer.py"

if [ -z "${TWELVE_DATA_API_KEY:-}" ]; then
  echo "ERROR: TWELVE_DATA_API_KEY is not set."
  exit 1
fi

for REQUIRED in "$UPDATER" "$GATE" "$OBSERVER"
do
  if [ ! -f "$REQUIRED" ]; then
    echo "ERROR: required component missing: $REQUIRED"
    exit 1
  fi
done

mkdir -p \
  "$TWELVE_BARS" \
  "$CANDIDATE_DIR/logs" \
  "$CANDIDATE_DIR/raw" \
  "$CANDIDATE_DIR/metadata"

CYCLE_ID=$(date -u +"%Y%m%dT%H%M%SZ")
LOG="$CANDIDATE_DIR/logs/twelve_shadow_cycle_${CYCLE_ID}.log"
WATERMARK_CHECK="$CANDIDATE_DIR/metadata/gate_watermark_${CYCLE_ID}.json"
LOCK_DIR="$CANDIDATE_DIR/metadata/.twelve_shadow.lock"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "ERROR: another Twelve Data shadow candidate cycle appears to be running."
  exit 1
fi

cleanup() {
  rm -rf "$LOCK_DIR"
}
trap cleanup EXIT INT TERM

exec > >(tee -a "$LOG") 2>&1

echo "========================================================================"
echo "KQTRL M005 v1.2f — TWELVE DATA GUARDED SHADOW CANDIDATE"
echo "========================================================================"
echo "Cycle ID: $CYCLE_ID"
echo "Mode: OBSERVATION ONLY"
echo "Canonical run: $CANONICAL_RUN"
echo "Candidate dir: $CANDIDATE_DIR"
echo "Staleness limit: $MAX_STALENESS_MINUTES minutes"
echo

echo "[1/4] Updating Twelve Data M5 bars"
PYTHONPATH=. python3 "$UPDATER" \
  --output-dir "$TWELVE_BARS" \
  --audit-dir "$CANDIDATE_DIR/raw" \
  --outputsize 1000

echo
echo "[2/4] Applying fail-closed freshness and integrity gate"
if ! PYTHONPATH=. python3 "$GATE" \
  --bars-dir "$TWELVE_BARS" \
  --max-staleness-minutes "$MAX_STALENESS_MINUTES" \
  --watermark-out "$WATERMARK_CHECK"
then
  echo
  echo "GUARDED STOP"
  echo "The Twelve Data candidate observer was NOT run."
  echo "Canonical M005 was NOT modified."
  exit 3
fi

echo
echo "[3/4] Running observation-only frozen shadow candidate"
PYTHONPATH=. python3 "$OBSERVER" \
  --bars-dir "$TWELVE_BARS" \
  --candidate-dir "$CANDIDATE_DIR" \
  --cycle-id "$CYCLE_ID"

echo
echo "[4/4] Finalising candidate audit"
rm -f "$WATERMARK_CHECK"

echo
echo "Twelve Data guarded shadow candidate completed."
echo "Canonical M005 was NOT modified."
echo "Log: $LOG"

#!/bin/bash
set -e

cd ~/Projects/Trading-app-

export PYTHONPATH=.
export POLYGON_API_KEY="0wbOXaTXqruPMHGZ6GKFqSvZeL4EnF6a"
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

RUN_DATE=$(date -u -v-1d +%F)
LOG_DATE=$(date -u +%F)

mkdir -p logs

LOG_FILE="logs/paper_run_${LOG_DATE}.log"
SUMMARY_FILE="logs/paper_summary.csv"

"$PYTHON_BIN" cli/backfill_polygon.py \
  --from "$RUN_DATE" \
  --to "$RUN_DATE" \
  --symbol GBPUSD \
  --timeframe 1m \
  --out ./data/market_candles \
  --api_key "$POLYGON_API_KEY" \
  > "$LOG_FILE" 2>&1

"$PYTHON_BIN" cli/resample_market_data.py \
  --symbol GBPUSD \
  --in_timeframe 1m \
  --out_timeframe 5m \
  --path ./data/market_candles \
  --out ./data/resampled \
  >> "$LOG_FILE" 2>&1

"$PYTHON_BIN" cli/side_filtered_backtest.py \
  --input ./data/resampled/GBPUSD_5m.csv \
  --fast 20 \
  --slow 50 \
  --start-hour 11 \
  --end-hour 12 \
  --vol-window 12 \
  --vol-threshold 0.0005 \
  --cost-per-turn 0.00005 \
  >> "$LOG_FILE" 2>&1

"$PYTHON_BIN" - <<'PY'
# existing summary-parser block here
PY

cat "$LOG_FILE"

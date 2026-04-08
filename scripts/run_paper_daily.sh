#!/bin/bash
set -e

PROJECT_ROOT="$HOME/Projects/Trading-app-"
LOG_DIR="$PROJECT_ROOT/logs"

cd "$PROJECT_ROOT"

export PYTHONPATH=.
export POLYGON_API_KEY="0wbOXaTXqruPMHGZ6GKFqSvZeL4EnF6a"
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

RUN_DATE=$(date -u -v-1d +%F)
LOG_DATE=$(date +%F)

mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/paper_run_${LOG_DATE}.log"
SUMMARY_FILE="$LOG_DIR/paper_summary.csv"

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

LOG_FILE="$LOG_FILE" SUMMARY_FILE="$SUMMARY_FILE" LOG_DATE="$LOG_DATE" "$PYTHON_BIN" - <<'PY'
import csv
import os
import re

log_file = os.environ["LOG_FILE"]
summary_file = os.environ["SUMMARY_FILE"]
log_date = os.environ["LOG_DATE"]

with open(log_file, "r", encoding="utf-8") as f:
    text = f.read()

patterns = {
    "both_total_return": r"Mode: both.*?Total return:\s*([-\d.]+)%",
    "both_final_equity": r"Mode: both.*?Final equity:\s*([-\d.]+)",
    "both_max_drawdown": r"Mode: both.*?Max drawdown:\s*([-\d.]+)%",
    "both_sharpe_proxy": r"Mode: both.*?Sharpe proxy:\s*([-\d.]+)",
    "both_buy_hold_return": r"Mode: both.*?Buy & hold return:\s*([-\d.]+)%",
    "long_total_return": r"Mode: long.*?Total return:\s*([-\d.]+)%",
    "short_total_return": r"Mode: short.*?Total return:\s*([-\d.]+)%",
}

row = {"run_date": log_date}

for key, pattern in patterns.items():
    m = re.search(pattern, text, flags=re.S)
    row[key] = m.group(1) if m else ""

file_exists = os.path.exists(summary_file)

with open(summary_file, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "run_date",
            "both_total_return",
            "both_final_equity",
            "both_max_drawdown",
            "both_sharpe_proxy",
            "both_buy_hold_return",
            "long_total_return",
            "short_total_return",
        ],
    )
    if not file_exists:
        writer.writeheader()
    writer.writerow(row)

print("Updated", summary_file)
print(row)
PY

cat "$LOG_FILE"

#!/bin/bash
set -e

cd ~/Projects/Trading-app-

export PYTHONPATH=.

RUN_DATE=$(date -u -v-1d +%F)
LOG_DATE=$(date -u +%F)

mkdir -p logs

LOG_FILE="logs/paper_run_${LOG_DATE}.log"
SUMMARY_FILE="logs/paper_summary.csv"

python3 cli/backfill_polygon.py \
  --from "$RUN_DATE" \
  --to "$RUN_DATE" \
  --symbol GBPUSD \
  --timeframe 1m \
  --out ./data/market_candles \
  --api_key "$POLYGON_API_KEY" \
  > "$LOG_FILE" 2>&1

python3 cli/resample_market_data.py \
  --symbol GBPUSD \
  --in_timeframe 1m \
  --out_timeframe 5m \
  --path ./data/market_candles \
  --out ./data/resampled \
  >> "$LOG_FILE" 2>&1

python3 cli/side_filtered_backtest.py \
  --input ./data/resampled/GBPUSD_5m.csv \
  --fast 20 \
  --slow 50 \
  --start-hour 11 \
  --end-hour 12 \
  --vol-window 12 \
  --vol-threshold 0.0005 \
  --cost-per-turn 0.00005 \
  >> "$LOG_FILE" 2>&1

python3 - <<'PY'
import csv
import os
import re

log_file = os.path.join("logs", f"paper_run_{os.popen('date -u +%F').read().strip()}.log")
summary_file = os.path.join("logs", "paper_summary.csv")

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

row = {"run_date": os.popen("date -u +%F").read().strip()}

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

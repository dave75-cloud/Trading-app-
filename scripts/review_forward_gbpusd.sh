#!/bin/bash
set -e

cd "$HOME/Projects/Trading-app-"
export PYTHONPATH=.

PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

"$PYTHON_BIN" cli/extract_trade_log.py \
  --input ./data/resampled/GBPUSD_5m.csv \
  --output ./data/backtest_ready/trade_log_gbpusd_forward.csv \
  --fast 20 \
  --slow 50 \
  --start-hour 11 \
  --end-hour 12 \
  --vol-window 12 \
  --vol-threshold 0.0005 \
  --cost-per-turn 0.00005

TRADE_COUNT=$("$PYTHON_BIN" - <<'PY'
import pandas as pd
df = pd.read_csv("./data/backtest_ready/trade_log_gbpusd_forward.csv")
print(len(df))
PY
)

echo "Forward trade count: $TRADE_COUNT"

if [ "$TRADE_COUNT" -ge 50 ]; then
  echo "=== 50+ trades reached: running attribution summary ==="
  "$PYTHON_BIN" cli/trade_attribution_summary.py \
    --input ./data/backtest_ready/trade_log_gbpusd_forward.csv
else
  echo "=== Not enough trades yet for full review ==="
fi


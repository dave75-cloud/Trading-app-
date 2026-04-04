#!/bin/bash
set -e

cd ~/Projects/Trading-app-

export PYTHONPATH=.
export POLYGON_API_KEY="0wbOXaTXqruPMHGZ6GKFqSvZeL4EnF6a"

TODAY=$(date -u -v-1d +%F)

python3 cli/backfill_polygon.py \
  --from "$TODAY" \
  --to "$TODAY" \
  --symbol GBPUSD \
  --timeframe 1m \
  --out ./data/market_candles \
  --api_key "0wbOXaTXqruPMHGZ6GKFqSvZeL4EnF6a"

python3 cli/resample_market_data.py \
  --symbol GBPUSD \
  --in_timeframe 1m \
  --out_timeframe 5m \
  --path ./data/market_candles \
  --out ./data/resampled

python3 cli/side_filtered_backtest.py \
  --input ./data/resampled/GBPUSD_5m.csv \
  --fast 20 \
  --slow 50 \
  --start-hour 11 \
  --end-hour 12 \
  --vol-window 12 \
  --vol-threshold 0.0005 \
  --cost-per-turn 0.00005

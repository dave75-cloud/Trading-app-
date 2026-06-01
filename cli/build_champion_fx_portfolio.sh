#!/bin/bash
set -e

PYTHONPATH=. python3 cli/filter_trade_log.py \
  --input ./data/backtest_ready/trade_log_gbpusd_sized.csv \
  --output ./data/backtest_ready/trade_log_gbpusd_hour11.csv \
  --entry-hour 11

PYTHONPATH=. python3 cli/filter_trade_log.py \
  --input ./data/backtest_ready/trade_log_usdjpy_sized.csv \
  --output ./data/backtest_ready/trade_log_usdjpy_short_hour11.csv \
  --side short \
  --entry-hour 11

PYTHONPATH=. python3 cli/filter_trade_log.py \
  --input ./data/backtest_ready/trade_log_audusd_sized.csv \
  --output ./data/backtest_ready/trade_log_audusd_min6_hour11.csv \
  --min-bars-held 6 \
  --entry-hour 11

PYTHONPATH=. python3 cli/portfolio_equity.py \
  --inputs \
    ./data/backtest_ready/trade_log_gbpusd_hour11.csv \
    ./data/backtest_ready/trade_log_usdjpy_short_hour11.csv \
    ./data/backtest_ready/trade_log_audusd_min6_hour11.csv \
  --output ./data/backtest_ready/portfolio_equity_fx_champion.csv

PYTHONPATH=. python3 cli/portfolio_stats.py \
  --input ./data/backtest_ready/portfolio_equity_fx_champion.csv



# GBPUSD Signal & Trade Assist — All-in-One (T1–T6)
Created: 20260211-230639

This repository combines everything we prepared:
- FastAPI inference API + paper-broker
- Polygon backfill CLI
- Backtest engine (monthly walk-forward)
- Model training + registry
- Terraform (S3, RDS, ECS Fargate, ALB stubs)
- Eightcap MT5 bridge (dry-run + place_order)
- AGENT_BRIEF.md for Codex/GitHub coding agents

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
make api
# open http://127.0.0.1:8080/health and /signals/latest?h=30m
```

## Signal dashboard (Streamlit)

Local (API must be running):
```bash
make dashboard
# open http://127.0.0.1:8501
```

Docker (API + dashboard + paper broker):
```bash
make up
# API:       http://127.0.0.1:8080
# Dashboard: http://127.0.0.1:8501
# Broker:    http://127.0.0.1:8081
```

## Tests (CI)

```bash
make test
```

Coverage is enforced (>=85%) via `pytest-cov`.

## Benchmark harness

```bash
make bench
```

## Data backfill
```bash
python cli/backfill_polygon.py --from 2025-01-01 --to 2025-01-07 --out ./data/market_candles --api_key YOUR_POLYGON_KEY
```

## Incremental candle updates

This re-downloads the latest UTC day and then fills forward to now:

```bash
export POLYGON_API_KEY=...
make update_candles
```

## Signal history + evaluation

`/signals/latest` persists each payload into a local sqlite db (default `./data/app.db`).

Endpoints:
- `/signals/history?days=30&h=30m`
- `/signals/evaluate?days=30&h=30m` (directional realized-outcome check)

## Backtest
```bash
python cli/backtest.py --data_dir ./data/market_candles --symbol GBPUSD --horizon 30m --out ./backtests/run_30m.json
```

## Train models
```bash
python models/train.py --data_dir ./data/market_candles
```

## Terraform
See `infra/terraform/README.md` for variables and example `plan` invocation.

## Phase 2 (Eightcap MT5)
See `mt5_bridge/bridge.py` for `dry_run()` and `place_order()` usage.

Safety latch:
- Default is **dry-run**.
- Live routing requires `live=True` *and* `MT5_LIVE_ENABLED=1` in the environment.

An orchestration wrapper lives in `services/execution.py` (CI-safe `dry_run()` + MT5 live toggle scaffolding).

Optional dependency:
```bash
pip install -r requirements-mt5.txt
```


## AWS deployment (optional)

If you want this running on the internet:
- Use `infra/terraform` (plan first; apply only when ready).
- See `infra/terraform/README.md` for plain-English steps.

## Champion Baseline (v3 — current)

Validated through Q1 2025 in-sample with April–May 2025 forward testing.

Parameters:
- fast = 20
- slow = 50
- execution window = 11:00–12:00 UTC
- volatility window = 12
- volatility threshold = 0.0005
- cost per turn = 0.00005
- both sides

Validation summary:
- Q1 2025: +0.5839%, Sharpe 2.64
- April 2025: +0.5947%, Sharpe 5.11
- May 2025: +0.0830%, Sharpe 1.46

Supersedes prior 11:00–14:00 baseline due to improved forward stability and materially lower drawdowns.

Note: side_filtered_backtest.py "Trades" counts execution events,
while extract_trade_log.py counts completed round-trip trades.
Use extractor for true trade count.

Paper deployment started via launchd on 2026-04-04.
Strategy frozen: Champion v3.
Next review checkpoint: after 10 trading sessions.
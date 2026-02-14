# AGENT_BRIEF.md — GBPUSD Signal & Trade Assist

You are an autonomous coding agent working on this repository. Your goal is to deliver the MVP described in the README and design spec, with a paper-trading pilot and a clean path to Phase‑2 execution via Eightcap MT5.

Follow the **Tasks & Acceptance Criteria** below. PR-first, small increments, tests where appropriate, no secrets in repo.

## Tasks & Acceptance

T1 — Polygon minute loader (flat files → Parquet)
- Implement authenticated downloader for Polygon FX minute aggregates.
- CLI: `python cli/backfill_polygon.py --from YYYY-MM-DD --to YYYY-MM-DD --out ./data/market_candles --api_key $POLY`
- Accept when ≥1 day downloads to Parquet with schema `ts,symbol,timeframe,o,h,l,c,v,source`; tests mock HTTP.

T2 — Backtest engine (walk‑forward)
- ATR(14), RSI(14), session flags (Tokyo/London/NY), burst/compression signals.
- Session-aware spread/slippage; intrabar TP/SL touch; partial fills for limits.
- Monthly walk-forward; JSON report with PnL, Sharpe, max DD, hit rate, attribution.
- Accept when `cli/backtest.py` runs and outputs metrics JSON on sample Parquet.

T3 — Train models + calibration + registry
- Feature builder (lags, ATR, RSI, realized vol, session flags).
- Train XGBoost & LightGBM per horizon; select by AUC/Brier; (optionally) Platt calibration.
- Monthly walk-forward; save artifacts under `./models_registry/gbpusd/<horizon>/<date>/`.
- Accept when `models/train.py` completes and writes `model.pkl`, `feature_spec.json`, `metadata.json` with AUC/Brier/thresholds.

T4 — Inference API wiring
- Load latest registry artifacts; build features from recent Parquet window.
- Return calibrated `p_up`, `E[Δp]`, regime weights, and bracket with 2% risk sizing.
- Accept when `/signals/latest?h=30m|2h` returns non-dummy probabilities and coherent bracket.

T5 — Terraform (S3, RDS, ECS, ALB)
- Root + modules for S3, RDS Postgres, ECS Fargate (api + broker), ALB. All network IDs/images are variables.
- Accept when `terraform plan` succeeds with example vars in `infra/terraform/README.md`.

T6 — Eightcap MT5 mapping (demo-safe)
- Implement `mt5_bridge.place_order()` (maps to `order_send`); add `dry_run()` validation.
- Accept when `dry_run()` returns valid request for demo symbol and documents retcodes/usage.

## Guardrails
- Ask before big downloads or new heavy deps.
- No secrets committed; read from env/Secrets Manager later.
- Logging: INFO level, redact sensitive values.

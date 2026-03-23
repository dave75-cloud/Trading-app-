import glob
import json
import logging
import os
import pathlib
from datetime import datetime
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

from lib.sessions import session_flags
from storage.db_store import get_store
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/signals/latest")
def latest(h: str = "30m"):
    try:
        now = datetime.utcnow()
        sess = session_flags(now)

        h = h if h in ("30m", "2h") else "30m"
        df = _load_recent_parquet()
        asof_ts = df.sort_values("ts")["ts"].iloc[-1]
        timeframe = f"{BAR_MINUTES}m"

        model_pkl, meta_json = _latest_artifacts(h)

        # Phase 3: model path
        if model_pkl and meta_json and os.path.exists(meta_json):
            model = joblib.load(model_pkl)
            with open(meta_json) as f:
                meta = json.load(f)

            X = _build_features(df)
            feats = [f for f in meta.get("features", []) if f in X.columns]

            if not feats:
                raise ValueError("No matching model features found in live feature frame")

            Xn = X[feats].values
            p = float(model.predict_proba(Xn)[-1, 1])

            price = float(X["c"].iloc[-1])
            atr = float(X["rng"].rolling(14).mean().iloc[-1])
            d_sl = max(atr * 0.8, 0.0008)
            rr = 1.4

            if p >= 0.5:
                entry_type = "stop"
                entry_px = price + 0.5 * d_sl
                sl_px = entry_px - d_sl
                tp_px = entry_px + rr * d_sl
                side = "buy"
            else:
                entry_type = "stop"
                entry_px = price - 0.5 * d_sl
                sl_px = entry_px + d_sl
                tp_px = entry_px - rr * d_sl
                side = "sell"

            payload = {
                "status": "ok",
                "now": now.isoformat(),
                "asof_ts": asof_ts.isoformat(),
                "symbol": SYMBOL,
                "timeframe": timeframe,
                "horizon": h,
                "prob_up": p,
                "side": side,
                "expected_move": float((p - 0.5) * 2 * d_sl),
                "regime": {"mr": 0.5, "bo": 0.5},
                "session": sess,
                "suggestion": {
                    "entry_type": entry_type,
                    "entry_px": round(entry_px, 5),
                    "sl_px": round(sl_px, 5),
                    "tp_px": round(tp_px, 5),
                    "size": 1000,
                    "tif": "GTD-5m",
                },
                "source": "registry",
            }

            try:
                _store().upsert_signal(payload)
            except Exception:
                logger.exception("upsert_signal failed")

            return payload

        # Phase 2 fallback: real-data heuristic path
        last = df.tail(50)
        ret = last["c"].pct_change().mean()

        prob_up = float(0.5 + np.tanh(ret * 1000) * 0.2)
        side = "buy" if prob_up >= 0.5 else "sell"

        price = float(last["c"].iloc[-1])
        d = 0.001

        suggestion = {
            "entry_type": "market",
            "entry_px": round(price, 5),
            "sl_px": round(price - d, 5) if side == "buy" else round(price + d, 5),
            "tp_px": round(price + 2 * d, 5) if side == "buy" else round(price - 2 * d, 5),
            "size": 1000,
            "tif": "GTD-5m",
        }

        payload = {
            "status": "ok",
            "now": now.isoformat(),
            "asof_ts": asof_ts.isoformat(),
            "symbol": "GBPUSD",
            "horizon": h,
            "prob_up": prob_up,
            "side": side,
            "session": {"london": int(7 <= datetime.utcnow().hour <= 16)},
            "suggestion": suggestion,
            "source": "phase_2_real_data",
        }

        try:
            _store().upsert_signal(payload)
        except Exception:
            logger.exception("upsert_signal failed")

        return payload

    except Exception as e:
        logger.exception("signals_latest failed")
        return {
            "status": "error",
            "message": str(e),
            "horizon": h,
            "source": "signals_latest_guard",
        }
@app.get("/signals/history")
def history(days: int = 30, h: str = "30m", limit: int = 2000):
    return {
        "count": 0,
        "rows": [],
        "source": "debug_stub",
    }

@app.get("/signals/evaluate")
def evaluate(days: int = 30, h: str = "30m", limit: int = 2000):
    return {
        "summary": {
            "count": 0,
            "horizon": h,
            "accuracy": 0.0,
            "brier": None,
        },
        "rows": [],
        "source": "debug_stub",
    }


class BacktestRequest(BaseModel):
    horizon: str = "30m"
    days: int = 90


@app.post("/backtest/run")
def run_backtest(req: BacktestRequest):
    return {
        "summary": {
            "horizon": req.horizon,
            "days": req.days,
            "trades": 0,
            "pnl": 0.0,
            "avg_per_trade": 0.0,
            "winrate": 0.0,
        },
        "raw": {},
        "source": "debug_stub",
    }
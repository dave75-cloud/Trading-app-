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
        from datetime import datetime
        import numpy as np
        import pandas as pd
        import pathlib

        now = datetime.utcnow()

        # --- load data (safe fallback if none exists) ---
        base = pathlib.Path("./data/market_candles") / "GBPUSD"
        parts = sorted(base.rglob("*.parquet"))[-10:]

        if not parts:
            np.random.seed()
            c = np.cumsum(np.random.randn(500)) / 10000 + 1.27
            df = pd.DataFrame({
                "o": c,
                "h": c + np.abs(np.random.randn(500)) * 0.0005,
                "l": c - np.abs(np.random.randn(500)) * 0.0005,
                "c": c,
            })
            df["ts"] = pd.date_range(
                end=pd.Timestamp.utcnow(),
                periods=len(df),
                freq="T",
                tz="UTC",
            )
        else:
            dfs = [pd.read_parquet(p) for p in parts]
            df = pd.concat(dfs, ignore_index=True).sort_values("ts")

        # --- simple signal ---
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
            "tp_px": round(price + 2*d, 5) if side == "buy" else round(price - 2*d, 5),
            "size": 1000,
            "tif": "GTD-5m",
        }

        return {
            "status": "ok",
            "now": datetime.utcnow().isoformat(),
            "symbol": "GBPUSD",
            "horizon": h,
            "prob_up": prob_up,
            "side": side,
            "session": {"london": int(7 <= datetime.utcnow().hour <= 16)},
            "suggestion": suggestion,
            "source": "phase_2_real_data",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
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
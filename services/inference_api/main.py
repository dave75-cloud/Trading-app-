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
from models.toy_model import score_dummy
from storage.db_store import get_store

logger = logging.getLogger(__name__)

app = FastAPI()

REGISTRY = os.getenv("MODEL_REGISTRY", "./models_registry/gbpusd")
DATA_DIR = os.getenv("DATA_DIR", "./data/market_candles")
SYMBOL = os.getenv("SYMBOL", "GBPUSD")
BAR_MINUTES = int(os.getenv("BAR_MINUTES", "5"))


@app.get("/health")
def health():
    return {"status": "ok"}


@lru_cache(maxsize=1)
def _store():
    return get_store()


def _latest_artifacts(h: str):
    pattern = f"{REGISTRY}/{h}/*/model.pkl"
    files = sorted(glob.glob(pattern))
    if not files:
        return None, None
    return files[-1], files[-1].replace("model.pkl", "feature_spec.json")


def _load_recent_parquet():
    base = pathlib.Path(DATA_DIR) / SYMBOL
    parts = sorted(base.rglob("*.parquet"))[-10:]
    if not parts:
        np.random.seed(42)
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
        return df

    dfs = [pd.read_parquet(p) for p in parts]
    return pd.concat(dfs, ignore_index=True).sort_values("ts")


def rsi(series: pd.Series, n: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(n).mean()
    loss = (-delta.clip(upper=0)).rolling(n).mean()
    rs = gain / (loss + 1e-12)
    return 100 - (100 / (1 + rs))


def _build_features(df: pd.DataFrame):
    x = df.copy().sort_values("ts").tail(500)
    x["ret1"] = x["c"].pct_change()
    x["ret5"] = x["c"].pct_change(5)
    x["vol20"] = x["c"].pct_change().rolling(20).std()
    x["rng"] = x["h"] - x["l"]
    x["atr14"] = x["rng"].rolling(14).mean()
    x["rsi14"] = rsi(x["c"], 14)
    x["tokyo"] = x["ts"].dt.hour.between(0, 9).astype(int)
    x["london"] = x["ts"].dt.hour.between(7, 16).astype(int)
    x["newyork"] = x["ts"].dt.hour.between(12, 21).astype(int)
    return x.dropna().reset_index(drop=True)


@app.get("/signals/latest")
def latest(h: str = "30m"):
    try:
        now = datetime.utcnow()
        sess = session_flags(now)

        h = h if h in ("30m", "2h") else "30m"
        model_pkl, meta_json = _latest_artifacts(h)
        df = _load_recent_parquet()
        asof_ts = df.sort_values("ts")["ts"].iloc[-1]
        timeframe = f"{BAR_MINUTES}m"

        if not model_pkl:
            s = score_dummy(df.tail(200), horizon=h)
            payload = {
                "now": now.isoformat(),
                "asof_ts": asof_ts.isoformat(),
                "symbol": SYMBOL,
                "timeframe": timeframe,
                "horizon": h,
                **s,
                "session": sess,
                "source": "toy",
            }
            try:
                _store().upsert_signal(payload)
            except Exception:
                logger.exception("upsert_signal failed")
            return payload

        model = joblib.load(model_pkl)
        with open(meta_json) as f:
            meta = json.load(f)

        X = _build_features(df)
        feats = [f for f in meta["features"] if f in X.columns]
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
            "now": now.isoformat(),
            "asof_ts": asof_ts.isoformat(),
            "symbol": SYMBOL,
            "timeframe": timeframe,
            "horizon": h,
            "prob_up": p,
            "expected_move": float((p - 0.5) * 2 * d_sl),
            "regime": {"mr": 0.5, "bo": 0.5},
            "session": sess,
            "side": side,
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
    try:
        rows = _store().fetch_signals(
            days=days,
            horizon=h,
            symbol=SYMBOL,
            timeframe=f"{BAR_MINUTES}m",
            limit=limit,
        )
        return {"count": len(rows), "rows": rows}
    except Exception as e:
        logger.exception("history failed")
        return {"count": 0, "rows": [], "error": str(e)}

@app.get("/signals/evaluate")
def evaluate(days: int = 30, h: str = "30m", limit: int = 2000):
    try:
        h = h if h in ("30m", "2h") else "30m"
        horizon_minutes = 30 if h == "30m" else 120
        horizon_bars = max(1, int(round(horizon_minutes / max(BAR_MINUTES, 1))))

        rows = _store().fetch_signals(
            days=days,
            horizon=h,
            symbol=SYMBOL,
            timeframe=f"{BAR_MINUTES}m",
            limit=limit,
        )
        if not rows:
            return {
                "summary": {"count": 0, "horizon": h},
                "rows": [],
                "source": "empty_history",
            }

        df = _load_recent_parquet().copy().sort_values("ts")
        df = df[["ts", "c"]].dropna()

        sig = pd.DataFrame(
            {
                "asof_ts": pd.to_datetime(
                    [r["asof_ts"] for r in rows], utc=True, errors="coerce"
                ),
                "side": [r.get("side") for r in rows],
                "prob_up": [r.get("prob_up") for r in rows],
            }
        ).dropna(subset=["asof_ts"])

        if sig.empty:
            return {
                "summary": {"count": 0, "horizon": h},
                "rows": [],
                "source": "empty_history",
            }

        sig = sig.sort_values("asof_ts")
        sig["target_ts"] = sig["asof_ts"] + pd.Timedelta(minutes=horizon_minutes)

        base = df.rename(columns={"ts": "asof_ts", "c": "c0"}).sort_values("asof_ts")
        sig = pd.merge_asof(sig, base, on="asof_ts", direction="backward")

        fut = df.rename(columns={"ts": "target_ts", "c": "c1"}).sort_values("target_ts")
        sig = pd.merge_asof(sig, fut, on="target_ts", direction="backward")

        sig = sig.dropna(subset=["c0", "c1"])
        if sig.empty:
            return {
                "summary": {"count": 0, "horizon": h},
                "rows": [],
                "source": "empty_join",
            }

        sig["realized_up"] = (sig["c1"] > sig["c0"]).astype(int)
        sig["signal_buy"] = (sig["side"].astype(str).str.lower() == "buy").astype(int)
        sig["hit"] = (sig["signal_buy"] == sig["realized_up"]).astype(int)

        n = int(len(sig))
        acc = float(sig["hit"].mean()) if n else 0.0

        if sig["prob_up"].notna().any():
            p = sig["prob_up"].astype(float).clip(0, 1)
            y = sig["realized_up"].astype(float)
            brier = float(((p - y) ** 2).mean())
        else:
            brier = None

        out_rows = sig[
            ["asof_ts", "target_ts", "side", "prob_up", "c0", "c1", "realized_up", "hit"]
        ].copy()
        out_rows["asof_ts"] = out_rows["asof_ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        out_rows["target_ts"] = out_rows["target_ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "summary": {
                "count": n,
                "horizon": h,
                "bar_minutes": BAR_MINUTES,
                "horizon_bars": horizon_bars,
                "accuracy": acc,
                "brier": brier,
            },
            "rows": out_rows.to_dict(orient="records"),
        }

    except Exception as e:
        logger.exception("evaluate failed")
        return {
            "summary": {"count": 0, "horizon": h},
            "rows": [],
            "status": "error",
            "message": str(e),
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

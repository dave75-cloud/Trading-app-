
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

logger = logging.getLogger(__name__)

app = FastAPI()

REGISTRY = os.getenv("MODEL_REGISTRY", "./models_registry/gbpusd")
DATA_DIR = os.getenv("DATA_DIR", "./data/market_candles")
SYMBOL = os.getenv("SYMBOL", "GBPUSD")
BAR_MINUTES = int(os.getenv("BAR_MINUTES", "5"))

logger.info(
    "Starting inference API | symbol=%s | data_dir=%s | registry=%s | bar_minutes=%s",
    SYMBOL, 
    DATA_DIR, 
    REGISTRY, 
    BAR_MINUTES,
)

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
            "symbol": SYMBOL,
            "timeframe": timeframe,
            "horizon": h,
            "prob_up": prob_up,
            "side": side,
            "ref_px": round(price, 5),
            "expected_move": float((prob_up - 0.5) * 2 * d),
            "regime": {"mr": 0.5, "bo": 0.5},
            "session": sess,
            "suggestion": suggestion,
            "source": "fallback",
        }

        try:
            _store().upsert_signal(payload)
        except Exception:
            logger.exception("upsert_signal failed")

        return payload

        payload = {
            "status": "ok",
            "now": now.isoformat(),
            "asof_ts": asof_ts.isoformat(),
            "symbol": SYMBOL,
            "timeframe": timeframe,
            "horizon": h,
            "prob_up": prob_up,
            "side": side,
            "ref_px": round(price, 5),
            "expected_move": float((prob_up - 0.5) * 2 * d),
            "regime": {"mr": 0.5, "bo": 0.5},
            "session": sess,
            "suggestion": suggestion,
            "source": "fallback",
        }

        try:
            _store().upsert_signal(payload)
        except Exception:
            logger.exception("upsert_signal failed")

        return payload

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
        rows = _store().get_signals(limit=limit * 2)

        filtered = [
            r for r in rows
            if r.get("horizon") == h
        ]

        filtered.sort(key=lambda r: r.get("asof_ts", ""), reverse=True)

        return {
            "count": len(filtered),
            "rows": filtered[:limit],
            "source": "store",
        }
    except Exception as e:
        logger.exception("signals_history failed")
        return {
            "count": 0,
            "rows": [],
            "source": "signals_history_guard",
            "message": str(e),
        }

@app.get("/signals/evaluate")
def evaluate(days: int = 30, h: str = "30m", limit: int = 2000):
    rows = _store().get_signals(limit=limit)

    if not rows:
        return {
            "summary": {
                "count": 0,
                "horizon": h,
                "accuracy": 0.0,
                "brier": None,
            },
            "rows": [],
            "source": "no_data",
        }

    df = _load_recent_parquet().sort_values("ts").copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"])

    horizon_minutes = {"30m": 30, "2h": 120}.get(h, 30)

    out = []
    correct = 0
    brier_sum = 0.0

    for r in rows:
        if r.get("horizon") != h:
            continue

        p = r.get("prob_up")
        ref_px = r.get("ref_px")
        asof_ts = r.get("asof_ts")

        if p is None or ref_px is None or asof_ts is None:
            continue

        ts = pd.to_datetime(asof_ts, utc=True, errors="coerce")
        if pd.isna(ts):
            continue

        target_ts = ts + pd.Timedelta(minutes=horizon_minutes)
        future = df[df["ts"] >= target_ts]
        if future.empty:
            continue

        future_px = float(future.iloc[0]["c"])
        y = 1 if future_px > float(ref_px) else 0
        pred = 1 if float(p) >= 0.5 else 0

        correct += int(pred == y)
        brier_sum += (float(p) - y) ** 2

        out.append({
            "asof_ts": asof_ts,
            "ref_px": ref_px,
            "future_px": round(future_px, 5),
            "prob_up": float(p),
            "actual_up": y,
            "pred_up": pred,
        })

    n = len(out)

    return {
        "summary": {
            "count": n,
            "horizon": h,
            "accuracy": round(correct / n, 4) if n else 0.0,
            "brier": round(brier_sum / n, 4) if n else None,
        },
        "rows": out[:50],
        "source": "computed_from_parquet",
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

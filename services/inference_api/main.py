import logging
from datetime import datetime
from functools import lru_cache

import joblib
import json
import glob
import os
import pathlib

import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

from backtest.engine import monthly_walkforward
from lib.sessions import session_flags
from models.toy_model import score_dummy
from storage.db_store import get_store

logger = logging.getLogger(__name__)

app = FastAPI(title="GBPUSD Signal & Trade Assist - Inference API")

REGISTRY = os.getenv("MODEL_REGISTRY", "./models_registry/gbpusd")
DATA_DIR = os.getenv("DATA_DIR", "./data/market_candles")
SYMBOL = os.getenv("SYMBOL", "GBPUSD")
BAR_MINUTES = int(os.getenv("BAR_MINUTES", "5"))


# -----------------------
# BASIC HEALTH (KEEP SIMPLE)
# -----------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------
# DEBUG STUB (CRITICAL TEST)
# -----------------------
@app.get("/signals/latest")
def signals_latest(h: str = "30m"):
    return {
        "status": "ok",
        "symbol": "GBPUSD",
        "horizon": h,
        "source": "debug_stub",
    }


# -----------------------
# STORE
# -----------------------
@lru_cache(maxsize=1)
def _store():
    return get_store()


# -----------------------
# MODELS / DATA
# -----------------------
class OrderSuggestion(BaseModel):
    entry_type: str
    entry_px: float
    sl_px: float
    tp_px: float
    size: int
    tif: str


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
            end=pd.Timestamp.utcnow(), periods=len(df), freq="T", tz="UTC"
        )
        return df

    dfs = [pd.read_parquet(p) for p in parts]
    return pd.concat(dfs, ignore_index=True).sort_values("ts")


def rsi(series: pd.Series, n: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.clip(lower=0)).rolling(n).mean()
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
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import pandas as pd, numpy as np, pathlib, glob, joblib, os, json
from models.toy_model import score_dummy
from lib.sessions import session_flags
from backtest.engine import monthly_walkforward
from functools import lru_cache
from storage.db_store import get_store


@lru_cache(maxsize=1)
def _store():
    # Resolve DB_URL/DB_PATH lazily so tests can set env vars before import.
    return get_store()

REGISTRY = os.getenv("MODEL_REGISTRY", "./models_registry/gbpusd")
DATA_DIR = os.getenv("DATA_DIR", "./data/market_candles")
SYMBOL = os.getenv("SYMBOL", "GBPUSD")
BAR_MINUTES = int(os.getenv("BAR_MINUTES", "5"))

app = FastAPI(title="GBPUSD Signal & Trade Assist - Inference API")

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
    if not files: return None, None
    return files[-1], files[-1].replace("model.pkl","feature_spec.json")

def _load_recent_parquet():
    base = pathlib.Path(DATA_DIR) / SYMBOL
    parts = sorted(base.rglob("*.parquet"))[-10:]
    if not parts:
        np.random.seed(42)
        c = np.cumsum(np.random.randn(500))/10000 + 1.27
        df = pd.DataFrame({"o":c,"h":c+np.abs(np.random.randn(500))*0.0005,"l":c-np.abs(np.random.randn(500))*0.0005,"c":c})
        df['ts'] = pd.date_range(end=pd.Timestamp.utcnow(), periods=len(df), freq='T', tz='UTC')
        return df
    dfs = [pd.read_parquet(p) for p in parts]
    return pd.concat(dfs, ignore_index=True).sort_values("ts")

def _build_features(df: pd.DataFrame):
    x = df.copy().sort_values('ts').tail(500)
    x['ret1'] = x['c'].pct_change()
    x['ret5'] = x['c'].pct_change(5)
    x['vol20'] = x['c'].pct_change().rolling(20).std()
    x['rng'] = x['h']-x['l']
    x['atr14'] = (x['rng'].rolling(14).mean())
    x['rsi14'] = rsi(x['c'],14)
    x['tokyo'] = x['ts'].dt.hour.between(0,9).astype(int)
    x['london'] = x['ts'].dt.hour.between(7,16).astype(int)
    x['newyork'] = x['ts'].dt.hour.between(12,21).astype(int)
    x = x.dropna().reset_index(drop=True)
    return x

def rsi(series: pd.Series, n: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.clip(lower=0)).rolling(n).mean()
    loss = (-delta.clip(upper=0)).rolling(n).mean()
    rs = gain / (loss + 1e-12)
    return 100 - (100 / (1 + rs))

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

@app.get("/signals/latest")
def latest(h: str = "30m"):
    now = datetime.utcnow(); sess = session_flags(now)
    model_pkl, meta_json = _latest_artifacts(h if h in ("30m","2h") else "30m")
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
        _store().upsert_signal(payload)
        return payload
    model = joblib.load(model_pkl); meta = json.load(open(meta_json))
    X = _build_features(df); feats = [f for f in meta["features"] if f in X.columns]
    Xn = X[feats].values
    p = float(model.predict_proba(Xn)[-1,1])
    price = float(X['c'].iloc[-1]); atr = float((X['rng'].rolling(14).mean().iloc[-1]))
    d_sl = max(atr*0.8, 0.0008); rr = 1.4
    if p >= 0.5:
        entry_type="stop"; entry_px=price+0.5*d_sl; sl_px=entry_px-d_sl; tp_px=entry_px+rr*d_sl; side="buy"
    else:
        entry_type="stop"; entry_px=price-0.5*d_sl; sl_px=entry_px+d_sl; tp_px=entry_px-rr*d_sl; side="sell"
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
    _store().upsert_signal(payload)
    return payload


@app.get("/signals/history")
def history(days: int = 30, h: str = "30m", limit: int = 2000):
    """Historical signals captured by /signals/latest.

    Returns an ordered list suitable for charting.
    """
    rows = _store().fetch_signals(days=days, horizon=h, symbol=SYMBOL, timeframe=f"{BAR_MINUTES}m", limit=limit)
    # keep payload lightweight by default
    out = [
        {
            "asof_ts": r["asof_ts"],
            "horizon": r["horizon"],
            "symbol": r["symbol"],
            "timeframe": r["timeframe"],
            "side": r.get("side"),
            "prob_up": r.get("prob_up"),
            "expected_move": r.get("expected_move"),
            "entry_px": r.get("entry_px"),
            "sl_px": r.get("sl_px"),
            "tp_px": r.get("tp_px"),
            "source": r.get("source"),
        }
        for r in rows
    ]
    return {"count": len(out), "rows": out}


@app.get("/signals/evaluate")
def evaluate(days: int = 30, h: str = "30m", limit: int = 2000):
    """Compare stored signals to realized outcomes on the candle series.

    This is a lightweight 'live-vs-realized' check for the dashboard.
    It does NOT re-run training; it only checks whether the *direction* implied by the
    signal was correct after the horizon.
    """
    h = h if h in ("30m", "2h") else "30m"
    horizon_minutes = 30 if h == "30m" else 120
    horizon_bars = max(1, int(round(horizon_minutes / max(BAR_MINUTES, 1))))

    rows = _store().fetch_signals(days=days, horizon=h, symbol=SYMBOL, timeframe=f"{BAR_MINUTES}m", limit=limit)
    if not rows:
        return {"summary": {"count": 0}, "rows": []}

    # Load enough candles to cover the evaluation window plus horizon.
    df = _load_recent_parquet().copy().sort_values("ts")
    df = df[["ts", "c"]].dropna()

    sig = pd.DataFrame(
        {
            "asof_ts": pd.to_datetime([r["asof_ts"] for r in rows], utc=True, errors="coerce"),
            "side": [r.get("side") for r in rows],
            "prob_up": [r.get("prob_up") for r in rows],
        }
    ).dropna(subset=["asof_ts"])
    if sig.empty:
        return {"summary": {"count": 0}, "rows": []}

    sig = sig.sort_values("asof_ts")
    sig["target_ts"] = sig["asof_ts"] + pd.Timedelta(minutes=horizon_minutes)

    # Map to nearest candle close at/just before asof, and at/just before target.
    base = df.rename(columns={"ts": "asof_ts", "c": "c0"}).sort_values("asof_ts")
    sig = pd.merge_asof(sig, base, on="asof_ts", direction="backward")
    fut = df.rename(columns={"ts": "target_ts", "c": "c1"}).sort_values("target_ts")
    sig = pd.merge_asof(sig, fut, on="target_ts", direction="backward")
    sig = sig.dropna(subset=["c0", "c1"])

    sig["realized_up"] = (sig["c1"] > sig["c0"]).astype(int)
    sig["signal_buy"] = (sig["side"].astype(str).str.lower() == "buy").astype(int)
    sig["hit"] = (sig["signal_buy"] == sig["realized_up"]).astype(int)

    # Metrics
    n = int(len(sig))
    acc = float(sig["hit"].mean()) if n else 0.0
    # brier score if prob_up present
    if sig["prob_up"].notna().any():
        p = sig["prob_up"].astype(float).clip(0, 1)
        y = sig["realized_up"].astype(float)
        brier = float(((p - y) ** 2).mean())
    else:
        brier = None

    out_rows = sig[["asof_ts", "target_ts", "side", "prob_up", "c0", "c1", "realized_up", "hit"]].copy()
    out_rows["asof_ts"] = out_rows["asof_ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out_rows["target_ts"] = out_rows["target_ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    summary = {
        "count": n,
        "horizon": h,
        "bar_minutes": BAR_MINUTES,
        "horizon_bars": horizon_bars,
        "accuracy": acc,
        "brier": brier,
    }
    return {"summary": summary, "rows": out_rows.to_dict(orient="records")}


class BacktestRequest(BaseModel):
    horizon: str = "30m"
    days: int = 90


@app.post("/backtest/run")
def run_backtest(req: BacktestRequest):
    """Bounded backtest for dashboard use.

    Uses the toy walk-forward backtest engine in backtest.engine on recent parquet.
    This is intended for exploratory validation only (NOT for live trading decisions).
    """
    h = req.horizon if req.horizon in ("30m", "2h") else "30m"
    days = max(1, min(int(req.days), 3650))

    df = _load_recent_parquet().copy()
    df = df.sort_values("ts")
    # bound by lookback
    end = df["ts"].max()
    start = end - pd.Timedelta(days=days)
    df = df[df["ts"] >= start]

    horizon_minutes = 30 if h == "30m" else 120
    horizon_bars = max(1, int(round(horizon_minutes / max(BAR_MINUTES, 1))))

    res = monthly_walkforward(df.rename(columns={"o":"o","h":"h","l":"l","c":"c","ts":"ts"}), horizon_bars=horizon_bars)
    trades = int(res.get("trades", 0))
    pnl = float(res.get("pnl", 0.0))
    winrate = float(res.get("winrate", 0.0))
    avg = float(pnl / max(trades, 1))
    summary = {
        "horizon": h,
        "days": days,
        "bar_minutes": BAR_MINUTES,
        "horizon_bars": horizon_bars,
        "trades": trades,
        "pnl": pnl,
        "avg_per_trade": avg,
        "winrate": winrate,
    }
    return {"summary": summary, "raw": res}

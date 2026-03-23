from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/signals/latest")
def latest(h: str = "30m"):
    try:
        # minimal safe payload to satisfy dashboard
        return {
            "status": "ok",
            "symbol": "GBPUSD",
            "horizon": h,
            "side": "buy",
            "prob_up": 0.55,
            "session": {"london": 1},
            "suggestion": {
                "entry_type": "market",
                "entry_px": 1.2700,
                "sl_px": 1.2690,
                "tp_px": 1.2720,
                "size": 1000,
                "tif": "GTD-5m",
            },
            "source": "phase_1_stub",
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
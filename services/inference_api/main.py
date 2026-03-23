from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/signals/latest")
def latest(h: str = "30m"):
    return {
        "status": "ok",
        "note": "THIS IS NEW CODE",
        "horizon": h
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
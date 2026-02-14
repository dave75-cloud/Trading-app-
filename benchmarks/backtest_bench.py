"""Tiny benchmark harness.

Goal: catch accidental quadratic blowups and provide a comparable wall-clock snapshot.
Not intended to be a rigorous microbenchmark.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from backtest.engine import monthly_walkforward


@dataclass
class BenchResult:
    rows: int
    horizon_bars: int
    seconds: float
    trades: int
    pnl: float
    winrate: float


def _synthetic_ohlc(n: int = 200_000, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # Roughly FX-ish micro-returns
    ret = rng.normal(loc=0.0, scale=0.00005, size=n)
    c = 1.27 + np.cumsum(ret)
    spread = np.abs(rng.normal(scale=0.00015, size=n))
    h = c + spread
    l = c - spread
    o = np.r_[c[0], c[:-1]]
    v = rng.integers(50, 500, size=n)
    ts = pd.date_range("2024-01-01", periods=n, freq="min", tz="UTC")
    return pd.DataFrame({"ts": ts, "o": o, "h": h, "l": l, "c": c, "v": v})


def run(rows: int = 200_000, horizon_bars: int = 6) -> BenchResult:
    df = _synthetic_ohlc(rows)
    t0 = time.perf_counter()
    out = monthly_walkforward(df, horizon_bars=horizon_bars)
    dt = time.perf_counter() - t0
    return BenchResult(
        rows=rows,
        horizon_bars=horizon_bars,
        seconds=float(dt),
        trades=int(out.get("trades", 0)),
        pnl=float(out.get("pnl", 0.0)),
        winrate=float(out.get("winrate", 0.0)),
    )


if __name__ == "__main__":
    r = run()
    print(json.dumps(asdict(r), indent=2, sort_keys=True))

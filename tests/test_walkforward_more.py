import numpy as np
import pandas as pd

from backtest.engine import monthly_walkforward, session_label


def test_session_label_off_hours():
    # 23:30Z is outside all defined sessions in the simplistic labeling.
    ts = pd.Timestamp("2026-02-12T23:30:00Z")
    assert session_label(ts) == "off"


def test_monthly_walkforward_produces_trades_on_synthetic_extremes():
    # Build a deterministic downtrend (low RSI), spanning several months,
    # and inject occasional very wide bars to satisfy rng > atr.
    n = 4000
    ts = pd.date_range("2025-01-01", periods=n, freq="1h", tz="UTC")
    c = 1.30 - np.linspace(0, 0.05, n)  # steady downtrend
    o = c.copy()
    h = c + 0.0002
    l = c - 0.0002
    # Very wide bars periodically
    for i in range(100, n, 250):
        h[i] = c[i] + 0.01
        l[i] = c[i] - 0.01
    df = pd.DataFrame({"ts": ts, "o": o, "h": h, "l": l, "c": c})

    res = monthly_walkforward(df, horizon_bars=6)
    assert "trades" in res and "pnl" in res and "winrate" in res
    assert res["trades"] >= 1

import pandas as pd

from backtest.engine import monthly_walkforward


def test_monthly_walkforward_produces_trades_on_synthetic_data():
    # Build ~4 months of daily candles with a deep selloff to drive RSI < 30
    start = pd.Timestamp("2024-01-01T00:00:00Z")
    n = 130
    ts = pd.date_range(start=start, periods=n, freq="D", tz="UTC")

    # price trend: flat then sharp down then mild recovery
    c = []
    px = 1.30
    for i in range(n):
        if 30 <= i < 60:
            px -= 0.01
        elif 60 <= i < 90:
            px += 0.002
        c.append(px)

    df = pd.DataFrame({"ts": ts})
    df["c"] = c
    df["o"] = df["c"].shift(1).fillna(df["c"])
    # baseline tight range
    df["h"] = df["c"] + 0.03
    df["l"] = df["c"] - 0.03
    # spike range on a few days to satisfy rng > atr
    for idx in [55, 56, 57, 80, 81]:
        df.loc[idx, "h"] = df.loc[idx, "c"] + 0.20
        df.loc[idx, "l"] = df.loc[idx, "c"] - 0.20

    res = monthly_walkforward(df, horizon_bars=2)
    assert "trades" in res
    assert int(res["trades"]) >= 1
    assert "pnl" in res

import pandas as pd

from services.execution import ExecutionService, ExecConfig


def _candles(n=500):
    ts = pd.date_range("2024-01-01", periods=n, freq="min", tz="UTC")
    c = pd.Series(range(n), dtype=float) / 10000 + 1.2
    df = pd.DataFrame(
        {
            "ts": ts,
            "o": c.shift(1).fillna(c.iloc[0]),
            "h": c + 0.0002,
            "l": c - 0.0002,
            "c": c,
            "v": 100,
        }
    )
    return df


def test_execution_dry_run_smoke():
    svc = ExecutionService(ExecConfig(symbol="GBPUSD", horizon_bars=6, mt5_live=False))
    out = svc.dry_run(_candles())
    assert out["symbol"] == "GBPUSD"
    assert "trades" in out and "pnl" in out and "winrate" in out


def test_execution_live_disabled_returns_safe_response():
    svc = ExecutionService(ExecConfig(mt5_live=False))
    out = svc.place_order("GBPUSD", "buy", "market", 1.0, 0.9, 1.1, 0.01)
    assert out["accepted"] is False
    assert out["dry"] is True
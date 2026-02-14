import tempfile

import pandas as pd
from pathlib import Path


def test_update_polygon_chunks_from_latest_day(monkeypatch):
    from cli import update_polygon

    calls = []

    def fake_download_range(api_key, date_from, date_to, out_dir, symbol="GBPUSD"):
        calls.append((date_from, date_to))
        return 1

    monkeypatch.setattr(update_polygon, "download_range", fake_download_range)

    with tempfile.TemporaryDirectory() as td:
        # last data is on 2024-01-02; update should start from 2024-01-02T00:00Z
        t = pd.Timestamp("2024-01-02T12:34:00Z")
        dt = str(t.date())
        p = f"{td}/GBPUSD/timeframe=1m/dt={dt}/{dt}.parquet"
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"ts": [t]}).to_parquet(p, index=False)

        # freeze 'now' to 2024-01-03T00:10Z by monkeypatching datetime
        class _DT:
            @staticmethod
            def now(tz=None):
                return pd.Timestamp("2024-01-03T00:10:00Z").to_pydatetime()

        monkeypatch.setattr(update_polygon, "datetime", _DT)

        n = update_polygon.update(api_key="KEY", out_dir=td, symbol="GBPUSD")
        assert n == len(calls)
        assert calls[0][0].startswith("2024-01-02")
        assert calls[-1][1].startswith("2024-01-03")

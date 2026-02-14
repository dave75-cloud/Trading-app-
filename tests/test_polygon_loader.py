import json
import tempfile

import pandas as pd
import responses

from ingest.polygon_loader import download_range, POLY_BASE


@responses.activate
def test_download_range_http_mocked_writes_parquet():
    # Minimal polygon-like payload
    ts = int(pd.Timestamp("2024-01-01T00:00:00Z").timestamp() * 1000)
    payload = {
        "results": [
            {"t": ts, "o": 1.0, "h": 1.1, "l": 0.9, "c": 1.05, "v": 123},
            {"t": ts + 60000, "o": 1.05, "h": 1.2, "l": 1.0, "c": 1.1, "v": 231},
        ]
    }

    # The function builds a URL with .../start/end?apiKey=...
    # We match via a prefix.
    responses.add(
        responses.GET,
        POLY_BASE
        + "/C:GBPUSD/range/1/minute/"
        + str(ts)
        + "/"
        + str(ts + 60000)
        + "?adjusted=true&sort=asc&limit=50000&apiKey=KEY",
        json=payload,
        status=200,
    )

    with tempfile.TemporaryDirectory() as td:
        n = download_range(api_key="KEY", date_from="2024-01-01", date_to="2024-01-01T00:01:00Z", out_dir=td, symbol="GBPUSD")
        assert n == 2
        # Ensure parquet partition exists
        # dt partition should be 2024-01-01
        p = (
            pd.read_parquet(f"{td}/GBPUSD/timeframe=1m/dt=2024-01-01/2024-01-01.parquet")
        )
        assert len(p) == 2
        assert set(p.columns) >= {"ts", "o", "h", "l", "c", "v", "symbol", "timeframe", "source"}

"""Incremental Polygon candle updater.

Reads the latest parquet partitions in DATA_DIR and downloads any missing minutes up to 'now'.

Usage:
  python cli/update_polygon.py --out ./data/market_candles --symbol GBPUSD --api_key ...

Notes:
  - Polygon agg endpoint is capped (limit=50000). We chunk by UTC day to stay safe.
  - This is intentionally conservative: it will re-download the last day to ensure completeness.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ingest.polygon_loader import download_range


def _find_latest_ts(out_dir: str, symbol: str) -> pd.Timestamp | None:
    base = Path(out_dir) / symbol
    parts = sorted(base.rglob("*.parquet"))
    if not parts:
        return None
    # only inspect last few for speed
    tail = parts[-10:]
    mx: pd.Timestamp | None = None
    for p in tail:
        try:
            df = pd.read_parquet(p, columns=["ts"])
            if len(df) == 0:
                continue
            t = pd.to_datetime(df["ts"], utc=True).max()
            if mx is None or t > mx:
                mx = t
        except Exception:
            continue
    return mx


def _day_chunks(start: pd.Timestamp, end: pd.Timestamp):
    # inclusive start, exclusive end
    start = start.tz_convert("UTC")
    end = end.tz_convert("UTC")
    cur = pd.Timestamp(start.date(), tz="UTC")
    while cur < end:
        nxt = cur + pd.Timedelta(days=1)
        yield cur, min(nxt, end)
        cur = nxt


def update(api_key: str, out_dir: str, symbol: str = "GBPUSD", from_date: str | None = None) -> int:
    out_dir = str(out_dir)
    now = pd.Timestamp(datetime.now(timezone.utc))
    latest = _find_latest_ts(out_dir, symbol)

    if latest is None:
        if not from_date:
            raise SystemExit("No existing data found. Provide --from YYYY-MM-DD to seed initial download.")
        start = pd.Timestamp(from_date, tz="UTC")
    else:
        # conservative: restart from the beginning of the latest day
        start = pd.Timestamp(latest.date(), tz="UTC")

    total = 0
    for d0, d1 in _day_chunks(start, now):
        # Polygon expects ms; download_range accepts ISO strings.
        total += int(
            download_range(
                api_key=api_key,
                date_from=d0.isoformat(),
                date_to=d1.isoformat(),
                out_dir=out_dir,
                symbol=symbol,
            )
        )
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", dest="out_dir", default=os.getenv("DATA_DIR", "./data/market_candles"))
    ap.add_argument("--symbol", default=os.getenv("SYMBOL", "GBPUSD"))
    ap.add_argument("--api_key", default=os.getenv("POLYGON_API_KEY"))
    ap.add_argument("--from", dest="from_date", default=None)
    args = ap.parse_args()
    if not args.api_key:
        raise SystemExit("Missing api key. Provide --api_key or set POLYGON_API_KEY.")
    rows = update(api_key=args.api_key, out_dir=args.out_dir, symbol=args.symbol, from_date=args.from_date)
    print(f"Updated {args.symbol} -> wrote {rows} rows")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from storage.market_data import gap_report, load_market_data, normalize_market_df


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--timeframe", default="1m")
    p.add_argument("--path", default="./data/market_candles")
    p.add_argument("--start", default=None)
    p.add_argument("--end", default=None)
    return p.parse_args()


def invalid_ohlc_count(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    mask = (
        (df["h"] < df["o"]) |
        (df["h"] < df["c"]) |
        (df["l"] > df["o"]) |
        (df["l"] > df["c"]) |
        (df["h"] < df["l"])
    )
    return int(mask.sum())


def main():
    ...
    df = load_market_data(...)

    daily_summary = []

    if not df.empty:
        tmp = df.copy()
        tmp["day"] = tmp["ts"].dt.strftime("%Y-%m-%d")

        for day, chunk in tmp.groupby("day"):
            daily_summary.append(
                {
                    "day": day,
                    "row_count": int(len(chunk)),
                    "first_ts": chunk["ts"].min().isoformat(),
                    "last_ts": chunk["ts"].max().isoformat(),
                }
            )

    report = {
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "daily_summary": daily_summary,
        "row_count": int(len(df)),
        "min_ts": None if df.empty else df["ts"].min().isoformat(),
        "max_ts": None if df.empty else df["ts"].max().isoformat(),
        "duplicate_count": duplicate_count,
        "gap_count": len(gaps),
        "null_count": null_count,
        "invalid_ohlc_count": invalid_ohlc_count,
        "latest_bar_age_minutes": None if df.empty else float(
            (pd.Timestamp.now(tz="UTC") - df["ts"].max())
            / pd.Timedelta(minutes=1)
        ),
        "sample_gaps": gaps[:10],
    }

    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
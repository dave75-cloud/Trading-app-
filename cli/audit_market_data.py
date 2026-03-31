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


def main() -> int:
    args = parse_args()
    df = load_market_data(
        root=args.path,
        symbol=args.symbol,
        timeframe=args.timeframe,
        start=args.start,
        end=args.end,
    )
    df = normalize_market_df(df)

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

    gaps = gap_report(df, args.timeframe)
    duplicates = 0 if df.empty else int(df.duplicated(subset=["ts", "symbol", "timeframe"]).sum())
    nulls = int(df.isna().sum().sum()) if not df.empty else 0

    report = {
        "symbol": args.symbol.upper(),
        "timeframe": args.timeframe,
        "row_count": int(len(df)),
        "min_ts": None if df.empty else df["ts"].min().isoformat(),
        "max_ts": None if df.empty else df["ts"].max().isoformat(),
        "duplicate_count": duplicates,
        "gap_count": int(len(gaps)),
        "null_count": nulls,
        "invalid_ohlc_count": invalid_ohlc_count(df),
        "latest_bar_age_minutes": None if df.empty else float((pd.Timestamp.now(tz="UTC") - df["ts"].max()) / pd.Timedelta(minutes=1)),
        "sample_gaps": gaps.head(20).to_dict(orient="records"),
        "daily_summary": daily_summary,
    }

    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
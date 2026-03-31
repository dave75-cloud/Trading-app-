import argparse
import json
import pandas as pd

from storage.market_data import load_market_data


def gap_report(df: pd.DataFrame, timeframe: str) -> list[dict]:
    if df.empty:
        return []

    expected_delta = pd.Timedelta(minutes=1)
    gaps = []

    ts = df["ts"].sort_values().reset_index(drop=True)

    for i in range(1, len(ts)):
        prev_ts = ts.iloc[i - 1]
        next_ts = ts.iloc[i]
        delta = next_ts - prev_ts

        if delta > expected_delta:
            gaps.append(
                {
                    "prev_ts": str(prev_ts),
                    "next_ts": str(next_ts),
                    "gap_minutes": float(delta / pd.Timedelta(minutes=1)),
                }
            )

    return gaps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--timeframe", required=True)
    ap.add_argument("--path", required=True)
    args = ap.parse_args()

    df = load_market_data(
        args.path,
        symbol=args.symbol,
        timeframe=args.timeframe,
    )

    gaps = gap_report(df, args.timeframe)
    duplicates = (
        0
        if df.empty
        else int(df.duplicated(subset=["ts", "symbol", "timeframe"]).sum())
    )
    nulls = int(df.isna().sum().sum()) if not df.empty else 0

    invalid_ohlc_count = 0
    if not df.empty:
        invalid_ohlc_count = int(
            (
                (df["h"] < df["l"])
                | (df["o"] > df["h"])
                | (df["o"] < df["l"])
                | (df["c"] > df["h"])
                | (df["c"] < df["l"])
            ).sum()
        )

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

    expected_gaps = [g for g in gaps if g["gap_minutes"] > 1000]
    unexpected_gaps = [g for g in gaps if g["gap_minutes"] <= 1000]

    report = {
        "symbol": args.symbol.upper(),
        "timeframe": args.timeframe,
        "daily_summary": daily_summary,
        "row_count": int(len(df)),
        "min_ts": None if df.empty else df["ts"].min().isoformat(),
        "max_ts": None if df.empty else df["ts"].max().isoformat(),
        "duplicate_count": duplicates,
        "gap_count": len(gaps),
        "expected_gap_count": len(expected_gaps),
        "unexpected_gap_count": len(unexpected_gaps),
        "null_count": nulls,
        "invalid_ohlc_count": invalid_ohlc_count,
        "latest_bar_age_minutes": None
        if df.empty
        else float(
            (pd.Timestamp.now(tz="UTC") - df["ts"].max())
            / pd.Timedelta(minutes=1)
        ),
        "sample_gaps": gaps[:10],
        "sample_unexpected_gaps": unexpected_gaps[:10],
    }

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
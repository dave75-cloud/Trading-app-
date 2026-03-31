import argparse
from pathlib import Path

import pandas as pd


DEFAULT_EXCLUDE_DAYS = {
    "2025-01-14",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--exclude-days", nargs="*", default=None)
    ap.add_argument("--drop-sunday-reopen", action="store_true")
    ap.add_argument("--min-bars-per-day", type=int, default=None)
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    df = pd.read_csv(in_path)

    if df.empty:
        print("Input dataset is empty")
        return 0

    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)

    df["day"] = df["ts"].dt.strftime("%Y-%m-%d")
    df["weekday"] = df["ts"].dt.dayofweek

    exclude_days = set(DEFAULT_EXCLUDE_DAYS)
    if args.exclude_days:
        exclude_days.update(args.exclude_days)

    df = df[~df["day"].isin(exclude_days)].copy()

    if args.drop_sunday_reopen:
        df = df[df["weekday"] != 6].copy()

    if args.min_bars_per_day is not None:
        counts = df.groupby("day").size()
        keep_days = counts[counts >= args.min_bars_per_day].index
        df = df[df["day"].isin(keep_days)].copy()

    df = df.drop(columns=["day", "weekday"]).reset_index(drop=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Wrote {len(df)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

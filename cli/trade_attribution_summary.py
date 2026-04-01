import argparse
from pathlib import Path

import pandas as pd


def summarise(df: pd.DataFrame) -> None:
    print("\nOVERALL")
    print(f"Trade count: {len(df)}")
    print(f"Win rate: {(df['net_return'] > 0).mean():.2%}")
    print(f"Average net return: {df['net_return'].mean():.4%}")
    print(f"Median net return: {df['net_return'].median():.4%}")
    print(f"Best trade: {df['net_return'].max():.4%}")
    print(f"Worst trade: {df['net_return'].min():.4%}")
    print(f"Average bars held: {df['bars_held'].mean():.2f}")

    print("\nBY SIDE")
    print(
        df.groupby("side")["net_return"]
        .agg(["count", "mean", "median", "min", "max"])
        .to_string()
    )

    print("\nBY ENTRY HOUR")
    by_hour = (
        df.groupby("entry_hour")["net_return"]
        .agg(["count", "mean", "median", "min", "max"])
        .sort_values("mean", ascending=False)
    )
    print(by_hour.to_string())

    print("\nBY ENTRY DAY")
    by_day = (
        df.groupby("entry_day")["net_return"]
        .agg(["count", "mean", "median", "min", "max"])
        .sort_values("mean", ascending=False)
    )
    print(by_day.to_string())

    print("\nBY HOLDING LENGTH")
    bins = pd.cut(
        df["bars_held"],
        bins=[0, 2, 5, 10, 100],
        labels=["1-2", "3-5", "6-10", "11+"],
        include_lowest=True,
    )

    by_hold = (
        df.groupby(bins)["net_return"]
        .agg(["count", "mean", "median", "min", "max"])
        .sort_values("mean", ascending=False)
    )
    print(by_hold.to_string())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    path = Path(args.input)
    df = pd.read_csv(path)

    df["entry_ts"] = pd.to_datetime(df["entry_ts"], utc=True)
    df["exit_ts"] = pd.to_datetime(df["exit_ts"], utc=True)

    df["entry_hour"] = df["entry_ts"].dt.hour
    df["entry_day"] = df["entry_ts"].dt.strftime("%Y-%m-%d")

    summarise(df)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

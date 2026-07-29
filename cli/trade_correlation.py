import argparse
from pathlib import Path

import pandas as pd


def print_matrix(title: str, matrix: pd.DataFrame) -> None:
    print(f"\n=== {title} ===")
    if matrix.empty:
        print("No data available.")
    else:
        print(matrix.round(3).to_string())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--top-days", type=int, default=20)
    ap.add_argument("--crowded-output", default=None)
    args = ap.parse_args()

    if args.top_days <= 0:
        raise SystemExit("--top-days must be greater than zero")

    df = pd.read_csv(args.input)

    required = {"entry_ts", "symbol", "side", "capped_return"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")

    df["entry_ts"] = pd.to_datetime(df["entry_ts"], utc=True, errors="coerce")
    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["capped_return"] = pd.to_numeric(df["capped_return"], errors="coerce")
    df = df.dropna(subset=["entry_ts", "symbol", "capped_return"])

    if df.empty:
        raise SystemExit("No valid trades found")

    df["entry_day"] = df["entry_ts"].dt.floor("D")

    daily = df.pivot_table(
        index="entry_day",
        columns="symbol",
        values="capped_return",
        aggfunc="sum",
    ).sort_index()

    zero_filled = daily.fillna(0.0)
    active_mask = daily.notna().astype(int)

    print_matrix(
        "ZERO-FILLED DAILY RETURN CORRELATION BY PAIR",
        zero_filled.corr(method="pearson"),
    )

    print_matrix(
        "JOINT-ACTIVE-DAY RETURN CORRELATION BY PAIR",
        daily.corr(method="pearson", min_periods=2),
    )

    print_matrix(
        "DAILY ACTIVITY CORRELATION BY PAIR",
        active_mask.corr(method="pearson"),
    )

    joint_counts = pd.DataFrame(
        index=daily.columns,
        columns=daily.columns,
        dtype=int,
    )

    for left in daily.columns:
        for right in daily.columns:
            joint_counts.loc[left, right] = int(
                (daily[left].notna() & daily[right].notna()).sum()
            )

    print("\n=== JOINT-ACTIVE-DAY SAMPLE COUNTS ===")
    print(joint_counts.to_string())

    day_summary = (
        df.groupby("entry_day")
        .agg(
            distinct_pairs=("symbol", "nunique"),
            trades=("symbol", "size"),
            summed_trade_return=("capped_return", "sum"),
        )
        .sort_index()
    )

    print("\n=== SAME-DAY PAIR PARTICIPATION DISTRIBUTION ===")
    print(
        day_summary["distinct_pairs"]
        .value_counts()
        .sort_index()
        .rename_axis("distinct_pairs")
        .to_string()
    )

    crowded = day_summary[day_summary["distinct_pairs"] >= 3].copy()
    crowded = crowded.sort_values(
        ["distinct_pairs", "trades", "summed_trade_return"],
        ascending=[False, False, False],
    )

    print("\n=== CROWDED-DAY SUMMARY ===")
    print(f"Trading days: {len(day_summary)}")
    print(f"Days with 3+ pairs entering trades: {len(crowded)}")
    print(f"Share of trading days crowded: {len(crowded) / len(day_summary):.2%}")

    if crowded.empty:
        print("No days with 3+ pairs entering trades.")
    else:
        print(f"\n=== TOP {min(args.top_days, len(crowded))} CROWDED DAYS ===")
        print(crowded.head(args.top_days).to_string())

        crowded_days = crowded.index
        details = (
            df[df["entry_day"].isin(crowded_days)]
            [["entry_ts", "symbol", "side", "capped_return"]]
            .sort_values(["entry_ts", "symbol"])
        )

        if args.crowded_output:
            out_path = Path(args.crowded_output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            details.to_csv(out_path, index=False)
            print(f"\nWrote full crowded-day trade detail to {out_path}")

    print(
        "\nNote: daily returns are arithmetic sums of completed trade returns "
        "allocated to each trade's UTC entry day. Same-day participation does "
        "not necessarily mean positions overlapped."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

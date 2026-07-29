import argparse
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["entry_ts"] = pd.to_datetime(df["entry_ts"])
    df["entry_day"] = df["entry_ts"].dt.date

    if "symbol" not in df.columns:
        raise SystemExit("No symbol column found. Rebuild portfolio_equity first.")

    daily = (
        df.pivot_table(
            index="entry_day",
            columns="symbol",
            values="capped_return",
            aggfunc="sum",
        )
        .fillna(0)
    )

    print("\n=== DAILY RETURN CORRELATION BY PAIR ===")
    print(daily.corr().round(3).to_string())

    print("\n=== SAME-DAY TRADE CLUSTERING ===")
    counts = df.groupby("entry_day")["symbol"].nunique()
    print(counts.value_counts().sort_index().to_string())

    print("\n=== DAYS WITH 3+ PAIRS TRADING ===")
    crowded_days = counts[counts >= 3].index
    print(df[df["entry_day"].isin(crowded_days)][["entry_ts", "symbol", "side", "capped_return"]].to_string(index=False))


if __name__ == "__main__":
    main()


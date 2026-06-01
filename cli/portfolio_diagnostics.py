import argparse
import pandas as pd


def max_streak(values, condition):
    best = 0
    cur = 0
    for v in values:
        if condition(v):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["entry_ts"] = pd.to_datetime(df["entry_ts"])
    df["entry_day"] = df["entry_ts"].dt.date

    if "symbol" not in df.columns:
        df["symbol"] = "UNKNOWN"

    eq = df["portfolio_equity"]
    dd = eq / eq.cummax() - 1
    rets = df["capped_return"]

    print("\n=== PORTFOLIO DIAGNOSTICS ===")
    print(f"Trades: {len(df)}")
    print(f"Final equity: {eq.iloc[-1]:.4f}")
    print(f"Total return: {(eq.iloc[-1] - 1):.2%}")
    print(f"Max drawdown: {dd.min():.2%}")
    print(f"Avg return/trade: {rets.mean():.4%}")
    print(f"Median return/trade: {rets.median():.4%}")
    print(f"Win rate: {(rets > 0).mean():.2%}")
    print(f"Best trade: {rets.max():.4%}")
    print(f"Worst trade: {rets.min():.4%}")
    print(f"Longest losing streak: {max_streak(rets, lambda x: x <= 0)}")
    print(f"Longest winning streak: {max_streak(rets, lambda x: x > 0)}")

    print("\n=== CONTRIBUTION BY SYMBOL ===")
    by_symbol = (
        df.groupby("symbol")
        .agg(
            trades=("capped_return", "size"),
            total_return_sum=("capped_return", "sum"),
            avg_return=("capped_return", "mean"),
            median_return=("capped_return", "median"),
            win_rate=("capped_return", lambda x: (x > 0).mean()),
            best=("capped_return", "max"),
            worst=("capped_return", "min"),
        )
        .sort_values("total_return_sum", ascending=False)
    )
    print(by_symbol.to_string())

    print("\n=== CONTRIBUTION BY MONTH ===")
    df["month"] = df["entry_ts"].dt.to_period("M").astype(str)
    by_month = (
        df.groupby("month")
        .agg(
            trades=("capped_return", "size"),
            return_sum=("capped_return", "sum"),
            avg_return=("capped_return", "mean"),
            median_return=("capped_return", "median"),
            win_rate=("capped_return", lambda x: (x > 0).mean()),
        )
    )
    print(by_month.to_string())

    print("\n=== TOP 10 WINNERS ===")
    cols = ["entry_ts", "symbol", "side", "capped_return", "portfolio_equity"]
    print(df.sort_values("capped_return", ascending=False)[cols].head(10).to_string(index=False))

    print("\n=== TOP 10 LOSERS ===")
    print(df.sort_values("capped_return", ascending=True)[cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()


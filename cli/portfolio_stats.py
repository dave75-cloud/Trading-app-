import argparse
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input)

    eq = df["portfolio_equity"]

    # drawdown
    running_max = eq.cummax()
    dd = eq / running_max - 1

    max_dd = dd.min()
    final_eq = eq.iloc[-1]

    # returns per trade
    rets = df["capped_return"]

    print("\n=== PORTFOLIO STATS ===")
    print(f"Trades: {len(df)}")
    print(f"Final equity: {final_eq:.4f}")
    print(f"Max drawdown: {max_dd:.4%}")
    print(f"Avg return/trade: {rets.mean():.4%}")
    print(f"Median return/trade: {rets.median():.4%}")
    print(f"Best trade: {rets.max():.4%}")
    print(f"Worst trade: {rets.min():.4%}")

if __name__ == "__main__":
    main()


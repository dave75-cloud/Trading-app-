import argparse
import pandas as pd


def stats(df, label):
    eq = (1 + df["capped_return"]).cumprod()
    dd = eq / eq.cummax() - 1

    print(f"\n=== {label} ===")
    print(f"Trades: {len(df)}")
    print(f"Final equity: {eq.iloc[-1]:.4f}")
    print(f"Total return: {eq.iloc[-1] - 1:.2%}")
    print(f"Max DD: {dd.min():.2%}")
    print(f"Avg return/trade: {df['capped_return'].mean():.4%}")
    print(f"Median return/trade: {df['capped_return'].median():.4%}")
    print(f"Win rate: {(df['capped_return'] > 0).mean():.2%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["entry_ts"] = pd.to_datetime(df["entry_ts"])

    if "symbol" not in df.columns:
        raise SystemExit("No symbol column found. Rebuild portfolio_equity first.")

    df = df.sort_values("entry_ts").reset_index(drop=True)

    stats(df, "ALL PAIRS")

    no_eurusd = df[df["symbol"] != "EURUSD"].copy()
    stats(no_eurusd, "EX EURUSD")

    print("\n=== SINGLE PAIR VARIANTS ===")
    for symbol in sorted(df["symbol"].unique()):
        stats(df[df["symbol"] == symbol].copy(), symbol)


if __name__ == "__main__":
    main()

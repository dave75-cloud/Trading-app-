import argparse
import os
import re
import pandas as pd


def infer_symbol(path: str) -> str:
    name = os.path.basename(path).lower()
    m = re.search(r"trade_log_([a-z]{6})_", name)
    if m:
        return m.group(1).upper()
    return "UNKNOWN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    dfs = []
    for path in args.inputs:
        df = pd.read_csv(path)
        df["entry_ts"] = pd.to_datetime(df["entry_ts"])
        df["symbol"] = infer_symbol(path)
        dfs.append(df)

    df = pd.concat(dfs).sort_values("entry_ts").reset_index(drop=True)
    df["portfolio_equity"] = (1 + df["capped_return"]).cumprod()
    df.to_csv(args.output, index=False)

    print(f"Wrote portfolio to {args.output}")
    print(f"Final equity: {df['portfolio_equity'].iloc[-1]:.4f}")
    print(f"Trades: {len(df)}")


if __name__ == "__main__":
    main()


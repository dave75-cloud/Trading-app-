import argparse

import numpy as np
import pandas as pd


def print_stats(df: pd.DataFrame, label: str) -> None:
    print(f"\n=== {label} ===")

    returns = pd.to_numeric(df["capped_return"], errors="coerce").dropna()

    if returns.empty:
        print("Trades: 0")
        print("No valid returns available.")
        return

    values = returns.to_numpy(dtype=float)

    if np.any(values <= -1.0):
        raise SystemExit(f"{label}: capped_return contains a value <= -100%")

    equity = np.cumprod(1.0 + values)
    equity_with_start = np.concatenate(([1.0], equity))
    peak = np.maximum.accumulate(equity_with_start)
    drawdown = equity_with_start / peak - 1.0

    print(f"Trades: {len(values)}")
    print(f"Final equity: {equity[-1]:.4f}")
    print(f"Total return: {equity[-1] - 1.0:.2%}")
    print(f"Max DD: {drawdown.min():.2%}")
    print(f"Avg return/trade: {values.mean():.4%}")
    print(f"Median return/trade: {np.median(values):.4%}")
    print(f"Win rate: {(values > 0).mean():.2%}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input)

    required = {"entry_ts", "symbol", "capped_return"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")

    df["entry_ts"] = pd.to_datetime(df["entry_ts"], utc=True, errors="coerce")
    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["capped_return"] = pd.to_numeric(df["capped_return"], errors="coerce")
    df = df.dropna(subset=["entry_ts", "symbol", "capped_return"])
    df = df.sort_values("entry_ts").reset_index(drop=True)

    if df.empty:
        raise SystemExit("No valid trades found")

    symbols = sorted(df["symbol"].unique())

    print("Portfolio model: sequential compounding of completed trade returns")

    print_stats(df, "ALL PAIRS")

    print("\n=== LEAVE-ONE-PAIR-OUT VARIANTS ===")
    for symbol in symbols:
        print_stats(df[df["symbol"] != symbol].copy(), f"EX {symbol}")

    print("\n=== SINGLE-PAIR VARIANTS ===")
    for symbol in symbols:
        print_stats(df[df["symbol"] == symbol].copy(), symbol)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

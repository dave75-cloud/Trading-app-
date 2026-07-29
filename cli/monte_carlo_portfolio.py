import argparse

import numpy as np
import pandas as pd


def max_drawdown(equity: np.ndarray) -> float:
    """Calculate maximum drawdown, including initial equity of 1.0."""
    equity_with_start = np.concatenate(([1.0], np.asarray(equity, dtype=float)))
    peak = np.maximum.accumulate(equity_with_start)
    drawdown = equity_with_start / peak - 1.0
    return float(drawdown.min())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--runs", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.runs <= 0:
        raise SystemExit("--runs must be greater than zero")

    df = pd.read_csv(args.input)

    if "capped_return" not in df.columns:
        raise SystemExit("Input does not contain a capped_return column")

    returns = (
        pd.to_numeric(df["capped_return"], errors="coerce")
        .dropna()
        .to_numpy(dtype=float)
    )

    if len(returns) == 0:
        raise SystemExit("No valid capped_return values found")

    if np.any(returns <= -1.0):
        raise SystemExit(
            "capped_return contains a value <= -100%, so equity cannot be compounded safely"
        )

    rng = np.random.default_rng(args.seed)

    finals = np.empty(args.runs, dtype=float)
    drawdowns = np.empty(args.runs, dtype=float)
    worst_streaks = np.empty(args.runs, dtype=int)

    for run in range(args.runs):
        sample = rng.choice(returns, size=len(returns), replace=True)
        equity = np.cumprod(1.0 + sample)

        finals[run] = equity[-1]
        drawdowns[run] = max_drawdown(equity)

        worst = 0
        current = 0
        for value in sample:
            if value < 0:
                current += 1
                worst = max(worst, current)
            else:
                current = 0

        worst_streaks[run] = worst

    print("\n=== MONTE CARLO PORTFOLIO ANALYSIS ===")
    print("Method: IID bootstrap of completed capped trade returns")
    print(f"Trades sampled per run: {len(returns)}")
    print(f"Runs: {args.runs}")
    print(f"Random seed: {args.seed}")
    print(f"Median final equity: {np.median(finals):.4f}")
    print(f"5th pct final equity: {np.percentile(finals, 5):.4f}")
    print(f"95th pct final equity: {np.percentile(finals, 95):.4f}")
    print(f"Median max DD: {np.median(drawdowns):.2%}")
    print(f"Adverse 5th pct max DD: {np.percentile(drawdowns, 5):.2%}")
    print(f"Worst simulated max DD: {drawdowns.min():.2%}")
    print(f"Median worst losing streak: {np.median(worst_streaks):.0f}")
    print(f"95th pct worst losing streak: {np.percentile(worst_streaks, 95):.0f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

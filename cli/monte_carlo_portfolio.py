import argparse
import numpy as np
import pandas as pd


def max_drawdown(equity):
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1
    return dd.min()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--runs", type=int, default=10000)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    r = df["capped_return"].dropna().to_numpy()

    finals = []
    drawdowns = []
    worst_streaks = []

    for _ in range(args.runs):
        sample = np.random.choice(r, size=len(r), replace=True)
        equity = np.cumprod(1 + sample)

        finals.append(equity[-1])
        drawdowns.append(max_drawdown(equity))

        streak = cur = 0
        for x in sample:
            if x <= 0:
                cur += 1
                streak = max(streak, cur)
            else:
                cur = 0
        worst_streaks.append(streak)

    finals = np.array(finals)
    drawdowns = np.array(drawdowns)
    worst_streaks = np.array(worst_streaks)

    print("\n=== MONTE CARLO PORTFOLIO ANALYSIS ===")
    print(f"Trades sampled per run: {len(r)}")
    print(f"Runs: {args.runs}")
    print(f"Median final equity: {np.median(finals):.4f}")
    print(f"5th pct final equity: {np.percentile(finals, 5):.4f}")
    print(f"95th pct final equity: {np.percentile(finals, 95):.4f}")
    print(f"Median max DD: {np.median(drawdowns):.2%}")
    print(f"5th pct max DD: {np.percentile(drawdowns, 5):.2%}")
    print(f"Worst max DD: {drawdowns.min():.2%}")
    print(f"Median worst losing streak: {np.median(worst_streaks):.0f}")
    print(f"95th pct worst losing streak: {np.percentile(worst_streaks, 95):.0f}")


if __name__ == "__main__":
    main()



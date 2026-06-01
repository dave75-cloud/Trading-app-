import argparse
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--notional", type=float, default=5.0)
    ap.add_argument("--max-loss", type=float, default=0.005)
    args = ap.parse_args()

    df = pd.read_csv(args.input)

    df["scaled_return"] = df["net_return"] * args.notional
    df["capped_return"] = df["scaled_return"].clip(lower=-args.max_loss)

    df["equity_curve"] = (1 + df["capped_return"]).cumprod()

    df.to_csv(args.output, index=False)

    print(f"Wrote sized trades to {args.output}")
    print(f"Final equity: {df['equity_curve'].iloc[-1]:.4f}")

if __name__ == "__main__":
    main()


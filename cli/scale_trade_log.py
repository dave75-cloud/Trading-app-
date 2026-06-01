import argparse
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--scale", type=float, required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input)

    for col in ["net_return", "gross_return", "scaled_return", "capped_return", "return", "pnl", "pnl_pct"]:
        if col in df.columns:
            df[col] = df[col] * args.scale
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} scaled trades to {args.output}")

if __name__ == "__main__":
    main()

import argparse
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--side", choices=["long", "short"])
    ap.add_argument("--min-bars-held", type=int)
    ap.add_argument("--entry-hour", type=int)
    args = ap.parse_args()

    df = pd.read_csv(args.input)

    if args.side:
        df = df[df["side"] == args.side]

    if args.min_bars_held is not None:
        df = df[df["bars_held"] >= args.min_bars_held]

    if args.entry_hour is not None:
        if "entry_hour" not in df.columns:
            if "entry_time" in df.columns:
                df["entry_hour"] = pd.to_datetime(df["entry_time"]).dt.hour
            elif "entry_ts" in df.columns:
                df["entry_hour"] = pd.to_datetime(df["entry_ts"]).dt.hour
            elif "timestamp" in df.columns:
                df["entry_hour"] = pd.to_datetime(df["timestamp"]).dt.hour
            else:
                raise ValueError(
                    f"No entry_hour column and no recognised timestamp column. "
                    f"Columns available: {list(df.columns)}"
                )

        df = df[df["entry_hour"] == args.entry_hour]

    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df)} trades to {args.output}")

if __name__ == "__main__":
    main()


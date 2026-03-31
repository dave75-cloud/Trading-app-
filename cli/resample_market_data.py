import argparse
from pathlib import Path

import pandas as pd

from storage.market_data import load_market_data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--in_timeframe", default="1m")
    ap.add_argument("--out_timeframe", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    df = load_market_data(
        root=args.path,
        symbol=args.symbol,
        timeframe=args.in_timeframe,
    )

    if df.empty:
        print("No data")
        return 0

    df = df.sort_values("ts").copy()
    df = df.set_index("ts")

    rule_map = {
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1H",
        "4h": "4H",
    }

    if args.out_timeframe not in rule_map:
        raise ValueError(f"Unsupported timeframe: {args.out_timeframe}")

    rule = rule_map[args.out_timeframe]

    out = (
        df.resample(rule)
        .agg(
            {
                "o": "first",
                "h": "max",
                "l": "min",
                "c": "last",
                "v": "sum",
            }
        )
        .dropna()
        .reset_index()
    )

    out["symbol"] = args.symbol.upper()
    out["timeframe"] = args.out_timeframe

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    file_path = out_dir / f"{args.symbol.upper()}_{args.out_timeframe}.csv"
    out.to_csv(file_path, index=False)

    print(f"Wrote {len(out)} rows to {file_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

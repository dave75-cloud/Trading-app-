import argparse, pathlib, pandas as pd, json
from backtest.engine import monthly_walkforward

def load_parquet_dir(data_dir: pathlib.Path, symbol: str) -> pd.DataFrame:
    base = data_dir / symbol
    parts = list(base.rglob("*.parquet"))
    if not parts:
        raise FileNotFoundError(f"No Parquet under {base}")
    dfs = [pd.read_parquet(p) for p in sorted(parts)]
    return pd.concat(dfs, ignore_index=True).sort_values("ts")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--horizon", default="30m", choices=["30m","2h"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    df = load_parquet_dir(pathlib.Path(args.data_dir), args.symbol)
    horizon_bars = 6 if args.horizon=="30m" else 24
    res = monthly_walkforward(df, horizon_bars=horizon_bars)
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print("Backtest summary:", res)

if __name__ == "__main__":
    main()

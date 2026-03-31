import argparse
import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--fast", type=int, default=20)
    ap.add_argument("--slow", type=int, default=50)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)

    df = df.sort_values("ts").reset_index(drop=True)

    df["fast_ma"] = df["c"].rolling(args.fast).mean()
    df["slow_ma"] = df["c"].rolling(args.slow).mean()

    df["signal"] = 0
    df.loc[df["fast_ma"] > df["slow_ma"], "signal"] = 1
    df.loc[df["fast_ma"] < df["slow_ma"], "signal"] = -1

    df["position"] = df["signal"].shift(1).fillna(0)

    df["ret"] = df["c"].pct_change().fillna(0)
    df["strategy_ret"] = df["position"] * df["ret"]

    df["equity_curve"] = (1 + df["strategy_ret"]).cumprod()

    total_return = df["equity_curve"].iloc[-1] - 1
    trades = int((df["position"].diff().abs() > 0).sum())

    print(f"Rows: {len(df)}")
    print(f"Trades: {trades}")
    print(f"Total return: {total_return:.4%}")
    print(f"Final equity: {df['equity_curve'].iloc[-1]:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

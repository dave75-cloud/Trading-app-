import argparse
import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--fast", type=int, default=20)
    ap.add_argument("--slow", type=int, default=50)
    ap.add_argument("--start-hour", type=int, default=7)
    ap.add_argument("--end-hour", type=int, default=20)
    ap.add_argument("--vol-window", type=int, default=12)
    ap.add_argument("--vol-threshold", type=float, default=0.0008)
    ap.add_argument("--cost-per-turn", type=float, default=0.00005)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values("ts").reset_index(drop=True)

    df["hour"] = df["ts"].dt.hour

    df["fast_ma"] = df["c"].rolling(args.fast).mean()
    df["slow_ma"] = df["c"].rolling(args.slow).mean()

    df["ret"] = df["c"].pct_change().fillna(0)
    df["rolling_vol"] = df["ret"].rolling(args.vol_window).std()

    df["raw_signal"] = 0
    df.loc[df["fast_ma"] > df["slow_ma"], "raw_signal"] = 1
    df.loc[df["fast_ma"] < df["slow_ma"], "raw_signal"] = -1

    session_mask = (df["hour"] >= args.start_hour) & (df["hour"] < args.end_hour)
    vol_mask = df["rolling_vol"] > args.vol_threshold

    df["signal"] = 0
    df.loc[session_mask & vol_mask, "signal"] = df.loc[session_mask & vol_mask, "raw_signal"]

    df["position"] = df["signal"].shift(1).fillna(0)

    df["strategy_ret"] = df["position"] * df["ret"]

    df["turnover"] = df["position"].diff().abs().fillna(0)
    df["strategy_ret_net"] = (
        df["strategy_ret"] - df["turnover"] * args.cost_per_turn
    )

    df["equity_curve"] = (1 + df["strategy_ret_net"]).cumprod()

    equity = df["equity_curve"]
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_drawdown = drawdown.min()

    sharpe_proxy = 0.0
    if df["strategy_ret_net"].std() > 0:
        sharpe_proxy = (
            df["strategy_ret_net"].mean()
            / df["strategy_ret_net"].std()
        ) * (252 * 24 * 12) ** 0.5

    buy_hold = (1 + df["ret"]).cumprod()
    buy_hold_return = buy_hold.iloc[-1] - 1

    total_return = df["equity_curve"].iloc[-1] - 1
    trades = int((df["position"].diff().abs() > 0).sum())
    active_rows = int((df["signal"] != 0).sum())

    print(f"Rows: {len(df)}")
    print(f"Trades: {trades}")
    print(f"Active signal rows: {active_rows}")
    print(f"Total return: {total_return:.4%}")
    print(f"Final equity: {df['equity_curve'].iloc[-1]:.4f}")
    print(f"Max drawdown: {max_drawdown:.4%}")
    print(f"Sharpe proxy: {sharpe_proxy:.4f}")
    print(f"Buy & hold return: {buy_hold_return:.4%}")
    print(
        f"Filters: hours={args.start_hour:02d}:00-{args.end_hour:02d}:00 UTC, "
        f"vol_window={args.vol_window}, vol_threshold={args.vol_threshold}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import pandas as pd


def run_backtest(
    df: pd.DataFrame,
    fast: int,
    slow: int,
    start_hour: int,
    end_hour: int,
    vol_window: int,
    vol_threshold: float,
    cost_per_turn: float,
    side_mode: str,
) -> dict:
    x = df.copy()

    x["hour"] = x["ts"].dt.hour
    x["fast_ma"] = x["c"].rolling(fast).mean()
    x["slow_ma"] = x["c"].rolling(slow).mean()
    x["ret"] = x["c"].pct_change().fillna(0)
    x["rolling_vol"] = x["ret"].rolling(vol_window).std()

    x["raw_signal"] = 0
    x.loc[x["fast_ma"] > x["slow_ma"], "raw_signal"] = 1
    x.loc[x["fast_ma"] < x["slow_ma"], "raw_signal"] = -1

    session_mask = (x["hour"] >= start_hour) & (x["hour"] < end_hour)
    vol_mask = x["rolling_vol"] > vol_threshold

    x["signal"] = 0
    x.loc[session_mask & vol_mask, "signal"] = x.loc[session_mask & vol_mask, "raw_signal"]

    if side_mode == "long":
        x.loc[x["signal"] < 0, "signal"] = 0
    elif side_mode == "short":
        x.loc[x["signal"] > 0, "signal"] = 0
    elif side_mode != "both":
        raise ValueError(f"Unsupported side_mode: {side_mode}")

    x["position"] = x["signal"].shift(1).fillna(0)
    x["strategy_ret"] = x["position"] * x["ret"]
    x["turnover"] = x["position"].diff().abs().fillna(0)
    x["strategy_ret_net"] = x["strategy_ret"] - x["turnover"] * cost_per_turn
    x["equity_curve"] = (1 + x["strategy_ret_net"]).cumprod()

    equity = x["equity_curve"]
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_drawdown = float(drawdown.min()) if len(drawdown) else 0.0

    sharpe_proxy = 0.0
    if x["strategy_ret_net"].std() and x["strategy_ret_net"].std() > 0:
        sharpe_proxy = float(
            (x["strategy_ret_net"].mean() / x["strategy_ret_net"].std()) * (252 * 24 * 12) ** 0.5
        )

    buy_hold = (1 + x["ret"]).cumprod()
    buy_hold_return = float(buy_hold.iloc[-1] - 1) if len(buy_hold) else 0.0

    total_return = float(equity.iloc[-1] - 1) if len(equity) else 0.0
    trades = int((x["position"].diff().abs() > 0).sum())
    active_rows = int((x["signal"] != 0).sum())

    return {
        "side_mode": side_mode,
        "rows": int(len(x)),
        "trades": trades,
        "active_rows": active_rows,
        "total_return": total_return,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
        "max_drawdown": max_drawdown,
        "sharpe_proxy": sharpe_proxy,
        "buy_hold_return": buy_hold_return,
    }


import argparse
import pandas as pd


def build_positions(signals, min_bars_held=None):
    positions = []
    current_position = 0
    bars_held = 0

    for current_signal in signals:
        positions.append(current_position)

        if current_position == 0:
            if current_signal != 0:
                current_position = current_signal
                bars_held = 0
            continue

        bars_held += 1

        min_hold_active = (
            min_bars_held is not None
            and bars_held < min_bars_held
        )

        if min_hold_active:
            continue

        if current_signal == 0:
            current_position = 0
            bars_held = 0
        elif current_signal != current_position:
            current_position = current_signal
            bars_held = 0

    return pd.Series(positions, dtype=float)


def run_backtest(
    df: pd.DataFrame,
    fast: int,
    slow: int,
    start_hour: int,
    end_hour: int,
    vol_window: int,
    vol_threshold: float,
    cost_per_turn: float,
    side_mode: str,
    min_bars_held: int | None = None,
) -> dict:
    x = df.copy()

    x["hour"] = x["ts"].dt.hour
    x["fast_ma"] = x["c"].rolling(fast).mean()
    x["slow_ma"] = x["c"].rolling(slow).mean()
    x["ret"] = x["c"].pct_change().fillna(0)
    x["rolling_vol"] = x["ret"].rolling(vol_window).std()

    x["raw_signal"] = 0
    x.loc[x["fast_ma"] > x["slow_ma"], "raw_signal"] = 1
    x.loc[x["fast_ma"] < x["slow_ma"], "raw_signal"] = -1

    session_mask = (x["hour"] >= start_hour) & (x["hour"] < end_hour)
    vol_mask = x["rolling_vol"] > vol_threshold

    x["signal"] = 0
    x.loc[session_mask & vol_mask, "signal"] = x.loc[session_mask & vol_mask, "raw_signal"]

    if side_mode == "long":
        x.loc[x["signal"] < 0, "signal"] = 0
    elif side_mode == "short":
        x.loc[x["signal"] > 0, "signal"] = 0
    elif side_mode != "both":
        raise ValueError(f"Unsupported side_mode: {side_mode}")

    if min_bars_held is None:
        x["position"] = x["signal"].shift(1).fillna(0)
    else:
        x["position"] = build_positions(
            x["signal"].tolist(),
            min_bars_held=min_bars_held,
        ).set_axis(x.index)

    x["strategy_ret"] = x["position"] * x["ret"]
    x["turnover"] = x["position"].diff().abs().fillna(0)
    x["strategy_ret_net"] = x["strategy_ret"] - x["turnover"] * cost_per_turn
    x["equity_curve"] = (1 + x["strategy_ret_net"]).cumprod()

    equity = x["equity_curve"]
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_drawdown = float(drawdown.min()) if len(drawdown) else 0.0

    sharpe_proxy = 0.0
    if x["strategy_ret_net"].std() and x["strategy_ret_net"].std() > 0:
        sharpe_proxy = float(
            (x["strategy_ret_net"].mean() / x["strategy_ret_net"].std()) * (252 * 24 * 12) ** 0.5
        )

    buy_hold = (1 + x["ret"]).cumprod()
    buy_hold_return = float(buy_hold.iloc[-1] - 1) if len(buy_hold) else 0.0

    total_return = float(equity.iloc[-1] - 1) if len(equity) else 0.0
    trades = int((x["position"].diff().abs() > 0).sum())
    active_rows = int((x["signal"] != 0).sum())

    return {
        "side_mode": side_mode,
        "rows": int(len(x)),
        "trades": trades,
        "active_rows": active_rows,
        "total_return": total_return,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
        "max_drawdown": max_drawdown,
        "sharpe_proxy": sharpe_proxy,
        "buy_hold_return": buy_hold_return,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--fast", type=int, default=20)
    ap.add_argument("--slow", type=int, default=50)
    ap.add_argument("--start-hour", type=int, default=7)
    ap.add_argument("--end-hour", type=int, default=21)
    ap.add_argument("--vol-window", type=int, default=12)
    ap.add_argument("--vol-threshold", type=float, default=0.0010)
    ap.add_argument("--cost-per-turn", type=float, default=0.00005)
    ap.add_argument("--min-bars-held", type=int, default=None)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values("ts").reset_index(drop=True)

    for side_mode in ["both", "long", "short"]:
        result = run_backtest(
            df=df,
            fast=args.fast,
            slow=args.slow,
            start_hour=args.start_hour,
            end_hour=args.end_hour,
            vol_window=args.vol_window,
            vol_threshold=args.vol_threshold,
            cost_per_turn=args.cost_per_turn,
            side_mode=side_mode,
            min_bars_held=args.min_bars_held,
        )

        print()
        print(f"Mode: {result['side_mode']}")
        print(f"Rows: {result['rows']}")
        print(f"Trades: {result['trades']}")
        print(f"Active signal rows: {result['active_rows']}")
        print(f"Total return: {result['total_return']:.4%}")
        print(f"Final equity: {result['final_equity']:.4f}")
        print(f"Max drawdown: {result['max_drawdown']:.4%}")
        print(f"Sharpe proxy: {result['sharpe_proxy']:.4f}")
        print(f"Buy & hold return: {result['buy_hold_return']:.4%}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

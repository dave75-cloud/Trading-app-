import argparse
import itertools
from pathlib import Path

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
) -> dict:
    x = df.copy()

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
        "fast": fast,
        "slow": slow,
        "start_hour": start_hour,
        "end_hour": end_hour,
        "vol_window": vol_window,
        "vol_threshold": vol_threshold,
        "cost_per_turn": cost_per_turn,
        "rows": int(len(x)),
        "trades": trades,
        "active_rows": active_rows,
        "total_return": total_return,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
        "max_drawdown": max_drawdown,
        "sharpe_proxy": sharpe_proxy,
        "buy_hold_return": buy_hold_return,
    }


def parse_int_list(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def parse_float_list(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--fast-list", default="10,20")
    ap.add_argument("--slow-list", default="40,50")
    ap.add_argument("--start-hours", default="7,8")
    ap.add_argument("--end-hours", default="20,21")
    ap.add_argument("--vol-window", type=int, default=12)
    ap.add_argument("--vol-thresholds", default="0.0005,0.0008,0.0010")
    ap.add_argument("--cost-per-turn", type=float, default=0.00005)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values("ts").reset_index(drop=True)
    df["hour"] = df["ts"].dt.hour

    fast_list = parse_int_list(args.fast_list)
    slow_list = parse_int_list(args.slow_list)
    start_hours = parse_int_list(args.start_hours)
    end_hours = parse_int_list(args.end_hours)
    vol_thresholds = parse_float_list(args.vol_thresholds)

    results = []
    for fast, slow, start_hour, end_hour, vol_threshold in itertools.product(
        fast_list, slow_list, start_hours, end_hours, vol_thresholds
    ):
        if fast >= slow:
            continue
        if start_hour >= end_hour:
            continue

        result = run_backtest(
            df=df,
            fast=fast,
            slow=slow,
            start_hour=start_hour,
            end_hour=end_hour,
            vol_window=args.vol_window,
            vol_threshold=vol_threshold,
            cost_per_turn=args.cost_per_turn,
        )
        results.append(result)

    out = pd.DataFrame(results)
    out = out.sort_values(
        by=["total_return", "sharpe_proxy", "max_drawdown"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    print(f"Wrote {len(out)} rows to {out_path}")
    if not out.empty:
        print("\nTop 10 results:")
        print(
            out[
                [
                    "fast",
                    "slow",
                    "start_hour",
                    "end_hour",
                    "vol_threshold",
                    "trades",
                    "total_return",
                    "max_drawdown",
                    "sharpe_proxy",
                ]
            ].head(10).to_string(index=False)
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

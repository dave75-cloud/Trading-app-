import argparse
from pathlib import Path

import pandas as pd


def build_signals(
    df: pd.DataFrame,
    fast: int,
    slow: int,
    start_hour: int,
    end_hour: int,
    vol_window: int,
    vol_threshold: float,
) -> pd.DataFrame:
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

    x["position"] = x["signal"].shift(1).fillna(0).astype(int)
    return x


def extract_trades(df: pd.DataFrame, cost_per_turn: float) -> pd.DataFrame:
    trades = []
    current_side = 0
    entry_idx = None
    entry_ts = None
    entry_px = None

    for i in range(1, len(df)):
        prev_pos = int(df.iloc[i - 1]["position"])
        curr_pos = int(df.iloc[i]["position"])

        if current_side == 0 and curr_pos != 0:
            current_side = curr_pos
            entry_idx = i
            entry_ts = df.iloc[i]["ts"]
            entry_px = float(df.iloc[i]["c"])
            continue

        if current_side != 0 and curr_pos != current_side:
            exit_ts = df.iloc[i]["ts"]
            exit_px = float(df.iloc[i]["c"])

            if current_side == 1:
                gross_return = (exit_px / entry_px) - 1.0
                side = "long"
            else:
                gross_return = (entry_px / exit_px) - 1.0
                side = "short"

            # one turn = entry + exit, so charge twice the per-turn-half assumption
            net_return = gross_return - (2 * cost_per_turn)
            bars_held = i - entry_idx

            trades.append(
                {
                    "entry_ts": entry_ts.isoformat(),
                    "exit_ts": exit_ts.isoformat(),
                    "side": side,
                    "entry_px": entry_px,
                    "exit_px": exit_px,
                    "gross_return": gross_return,
                    "net_return": net_return,
                    "bars_held": bars_held,
                }
            )

            if curr_pos != 0:
                current_side = curr_pos
                entry_idx = i
                entry_ts = df.iloc[i]["ts"]
                entry_px = float(df.iloc[i]["c"])
            else:
                current_side = 0
                entry_idx = None
                entry_ts = None
                entry_px = None

    return pd.DataFrame(trades)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--fast", type=int, default=20)
    ap.add_argument("--slow", type=int, default=50)
    ap.add_argument("--start-hour", type=int, default=7)
    ap.add_argument("--end-hour", type=int, default=21)
    ap.add_argument("--vol-window", type=int, default=12)
    ap.add_argument("--vol-threshold", type=float, default=0.0010)
    ap.add_argument("--cost-per-turn", type=float, default=0.00005)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values("ts").reset_index(drop=True)

    signal_df = build_signals(
        df=df,
        fast=args.fast,
        slow=args.slow,
        start_hour=args.start_hour,
        end_hour=args.end_hour,
        vol_window=args.vol_window,
        vol_threshold=args.vol_threshold,
    )

    trades = extract_trades(signal_df, cost_per_turn=args.cost_per_turn)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out_path, index=False)

    print(f"Wrote {len(trades)} trades to {out_path}")

    if not trades.empty:
        wins = int((trades["net_return"] > 0).sum())
        losses = int((trades["net_return"] <= 0).sum())
        win_rate = wins / len(trades)

        print(f"Wins: {wins}")
        print(f"Losses: {losses}")
        print(f"Win rate: {win_rate:.2%}")
        print(f"Average net return/trade: {trades['net_return'].mean():.4%}")
        print(f"Median net return/trade: {trades['net_return'].median():.4%}")
        print(f"Best trade: {trades['net_return'].max():.4%}")
        print(f"Worst trade: {trades['net_return'].min():.4%}")
        print(f"Average bars held: {trades['bars_held'].mean():.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
KQTRL M005 v1.2 — prospective frozen-strategy signal generator.

Frozen signal logic replicated from the audited research specification:
- 5-minute bars
- fast moving average: 20 bars
- slow moving average: 50 bars
- volatility lookback: 12 bars
- minimum volatility threshold: 0.0005
- session windows are start-inclusive and end-exclusive
- zero signal outside session or below volatility threshold
- one-bar delayed position
- minimum hold: 3 bars
- entry/exit execution reference: next bar close

This script only emits signals whose decision bar is the latest fully available
bar in the supplied data. It does not reconstruct older missed signals.

Expected bar files:
    <bars-dir>/AUDUSD_5m.csv
    <bars-dir>/EURUSD_5m.csv
    <bars-dir>/GBPUSD_5m.csv
    <bars-dir>/USDJPY_5m.csv

Required columns:
    ts, o, h, l, c

Output:
    M005 same-day signal input CSV suitable for capture_m005_signals.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import pandas as pd


PAIR_SESSIONS = {
    "AUDUSD": (11, 14),
    "EURUSD": (11, 13),
    "GBPUSD": (11, 13),
    "USDJPY": (11, 13),
}

FAST_MA = 20
SLOW_MA = 50
VOL_LOOKBACK = 12
VOL_THRESHOLD = 0.0005
MIN_HOLD_BARS = 3


def load_bars(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"ts", "o", "h", "l", "c"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{path} missing columns: {sorted(missing)}")

    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="raise")
    for col in ["o", "h", "l", "c"]:
        df[col] = pd.to_numeric(df[col], errors="raise")

    df = (
        df.sort_values("ts")
        .drop_duplicates("ts")
        .reset_index(drop=True)
    )
    return df


def derive_state(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    out = df.copy()

    out["fast_ma"] = out["c"].rolling(FAST_MA, min_periods=FAST_MA).mean()
    out["slow_ma"] = out["c"].rolling(SLOW_MA, min_periods=SLOW_MA).mean()
    out["ret"] = out["c"].pct_change()
    out["volatility"] = (
        out["ret"]
        .rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK)
        .std()
    )

    start_hour, end_hour = PAIR_SESSIONS[symbol]
    out["in_session"] = (
        (out["ts"].dt.hour >= start_hour)
        & (out["ts"].dt.hour < end_hour)
    )
    out["vol_ok"] = out["volatility"] >= VOL_THRESHOLD

    out["raw_signal"] = 0
    long_mask = (
        out["in_session"]
        & out["vol_ok"]
        & (out["fast_ma"] > out["slow_ma"])
    )
    short_mask = (
        out["in_session"]
        & out["vol_ok"]
        & (out["fast_ma"] < out["slow_ma"])
    )
    out.loc[long_mask, "raw_signal"] = 1
    out.loc[short_mask, "raw_signal"] = -1

    # One-bar delayed position.
    out["delayed_signal"] = out["raw_signal"].shift(1).fillna(0).astype(int)

    return out


def load_open_state(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_open_state(path: Path, state: Dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def infer_signal(
    symbol: str,
    df: pd.DataFrame,
    open_state: Dict[str, dict],
) -> dict | None:
    if len(df) < SLOW_MA + 2:
        return None

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    latest_ts = latest["ts"]
    previous_ts = previous["ts"]

    desired = int(latest["delayed_signal"])
    prev_desired = int(previous["delayed_signal"])

    state = open_state.get(symbol)
    current_side = 0 if state is None else int(state["side"])
    bars_held = 0 if state is None else int(state["bars_held"])

    event = None

    if current_side == 0:
        if desired in (1, -1) and desired != prev_desired:
            event = {
                "event_type": "entry",
                "side": "long" if desired == 1 else "short",
                "decision_timestamp": latest_ts,
                "expected_entry_timestamp": latest_ts,
                "model_entry_price": float(latest["c"]),
                "bars_held_before_event": 0,
            }
            open_state[symbol] = {
                "side": desired,
                "bars_held": 0,
                "entry_ts": latest_ts.isoformat(),
                "entry_px": float(latest["c"]),
            }
    else:
        bars_held += 1
        open_state[symbol]["bars_held"] = bars_held

        exit_due = desired == 0 or desired == -current_side
        if exit_due and bars_held >= MIN_HOLD_BARS:
            event = {
                "event_type": "exit",
                "side": "long" if current_side == 1 else "short",
                "decision_timestamp": latest_ts,
                "expected_entry_timestamp": latest_ts,
                "model_entry_price": float(latest["c"]),
                "bars_held_before_event": bars_held,
            }
            open_state.pop(symbol, None)

    if event is None:
        return None

    event.update({
        "symbol": symbol,
        "decision_bar_timestamp": previous_ts.isoformat(),
        "fast_ma": float(latest["fast_ma"]),
        "slow_ma": float(latest["slow_ma"]),
        "volatility": float(latest["volatility"]),
        "raw_signal": int(latest["raw_signal"]),
        "delayed_signal": desired,
    })
    return event


def executable_price(
    side: str,
    bid: float,
    ask: float,
) -> float:
    return ask if side == "long" else bid


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars-dir", required=True)
    ap.add_argument("--output-signals", required=True)
    ap.add_argument("--output-events", required=True)
    ap.add_argument("--state-file", required=True)
    ap.add_argument("--as-of", required=False)
    ap.add_argument(
        "--spread-bps",
        type=float,
        default=1.0,
        help="Fallback synthetic full spread in basis points when no bid/ask is provided.",
    )
    args = ap.parse_args()

    bars_dir = Path(args.bars_dir)
    state_file = Path(args.state_file)
    open_state = load_open_state(state_file)

    as_of = (
        pd.Timestamp(args.as_of, tz="UTC")
        if args.as_of
        else pd.Timestamp.now(tz="UTC")
    )

    signal_rows = []
    event_rows = []

    for symbol in PAIR_SESSIONS:
        path = bars_dir / f"{symbol}_5m.csv"
        if not path.exists():
            raise SystemExit(f"Missing required bar file: {path}")

        bars = load_bars(path)
        bars = bars[bars["ts"] <= as_of].copy()
        if bars.empty:
            continue

        derived = derive_state(bars, symbol)
        event = infer_signal(symbol, derived, open_state)
        if event is None:
            continue

        event_rows.append(event)

        if event["event_type"] != "entry":
            continue

        model_px = float(event["model_entry_price"])
        half_spread = model_px * (args.spread_bps / 10000.0) / 2.0
        bid = model_px - half_spread
        ask = model_px + half_spread
        side = event["side"]
        exec_px = executable_price(side, bid, ask)

        signal_id = (
            f"{symbol}_{event['decision_timestamp'].strftime('%Y%m%dT%H%M%SZ')}_"
            f"{side}"
        )

        signal_rows.append({
            "signal_id": signal_id,
            "symbol": symbol,
            "side": side,
            "signal_timestamp": event["decision_timestamp"].isoformat(),
            "expected_entry_timestamp": event["expected_entry_timestamp"].isoformat(),
            "model_entry_price": model_px,
            "observed_bid": bid,
            "observed_ask": ask,
            "executable_entry_price": exec_px,
        })

    save_open_state(state_file, open_state)

    signal_df = pd.DataFrame(
        signal_rows,
        columns=[
            "signal_id",
            "symbol",
            "side",
            "signal_timestamp",
            "expected_entry_timestamp",
            "model_entry_price",
            "observed_bid",
            "observed_ask",
            "executable_entry_price",
        ],
    )
    event_df = pd.DataFrame(event_rows)

    Path(args.output_signals).parent.mkdir(parents=True, exist_ok=True)
    signal_df.to_csv(args.output_signals, index=False)
    event_df.to_csv(args.output_events, index=False)

    print(f"As of: {as_of.isoformat()}")
    print(f"Entry signals generated: {len(signal_df)}")
    print(f"All events generated: {len(event_df)}")
    print(f"Signal file: {args.output_signals}")
    print(f"Event audit: {args.output_events}")
    print(f"State file: {state_file}")

    if signal_df.empty:
        print("No new prospective entry signal on the latest fully available bars.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

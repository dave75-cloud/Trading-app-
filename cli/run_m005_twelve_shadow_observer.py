#!/usr/bin/env python3
"""
KQTRL M005 v1.2f — Twelve Data guarded shadow candidate observer.

Observation-only:
- reads provider-specific Twelve Data M5 bars;
- processes only bars newer than the candidate watermark;
- reproduces frozen MA20/MA50, vol12 >= 0.0005 and pair-specific sessions;
- applies one-bar delayed desired position;
- enforces minimum hold of 3 bars before exit/reversal;
- writes candidate events and state to a separate audit stream;
- never writes canonical M005 signals, positions, ledger, eligibility counts,
  or status reports.

This is a provider-validation shadow, not an authorised M005 execution stream.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
FAST = 20
SLOW = 50
VOL_WINDOW = 12
VOL_THRESHOLD = 0.0005
MIN_HOLD_BARS = 3


def session_hours(pair: str) -> tuple[int, int]:
    if pair == "AUDUSD":
        return 11, 14
    return 11, 13


def load_bars(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Missing bars file: {path}")

    df = pd.read_csv(path)
    if df.empty:
        raise SystemExit(f"Empty bars file: {path}")

    required = {"ts", "o", "h", "l", "c"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{path} missing columns: {sorted(missing)}")

    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="raise")
    for col in ("o", "h", "l", "c"):
        df[col] = pd.to_numeric(df[col], errors="raise")

    return (
        df[["ts", "o", "h", "l", "c"]]
        .sort_values("ts")
        .drop_duplicates("ts", keep="last")
        .reset_index(drop=True)
    )


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def add_indicators(df: pd.DataFrame, pair: str) -> pd.DataFrame:
    out = df.copy()
    out["ret"] = out["c"].pct_change()
    out["fast_ma"] = out["c"].rolling(FAST, min_periods=FAST).mean()
    out["slow_ma"] = out["c"].rolling(SLOW, min_periods=SLOW).mean()
    out["vol"] = (
        out["ret"]
        .rolling(VOL_WINDOW, min_periods=VOL_WINDOW)
        .std(ddof=0)
    )

    start, end = session_hours(pair)
    out["in_session"] = (
        (out["ts"].dt.hour >= start)
        & (out["ts"].dt.hour < end)
        & (out["ts"].dt.dayofweek < 5)
    )
    out["vol_ok"] = out["vol"] >= VOL_THRESHOLD
    ready = (
        out["fast_ma"].notna()
        & out["slow_ma"].notna()
        & out["vol"].notna()
    )

    out["raw_signal"] = 0
    long_mask = (
        ready
        & out["in_session"]
        & out["vol_ok"]
        & (out["fast_ma"] > out["slow_ma"])
    )
    short_mask = (
        ready
        & out["in_session"]
        & out["vol_ok"]
        & (out["fast_ma"] < out["slow_ma"])
    )
    out.loc[long_mask, "raw_signal"] = 1
    out.loc[short_mask, "raw_signal"] = -1
    out["delayed_signal"] = out["raw_signal"].shift(1).fillna(0).astype(int)
    return out


def position_name(value: int) -> str:
    return {1: "long", -1: "short", 0: "flat"}[int(value)]


def _process_pair_original(
    pair: str,
    bars: pd.DataFrame,
    pair_state: dict[str, Any],
    last_processed: pd.Timestamp | None,
    cycle_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], pd.Timestamp | None]:
    enriched = add_indicators(bars, pair)

    if last_processed is None:
        # First observation cycle establishes a prospective boundary.
        newest = enriched["ts"].max()
        pair_state.setdefault("position", 0)
        pair_state.setdefault("bars_held", 0)
        pair_state.setdefault("entry_ts", "")
        pair_state.setdefault("entry_price", None)
        pair_state["last_observed_signal"] = int(
            enriched.loc[enriched["ts"] == newest, "delayed_signal"].iloc[-1]
        )
        return [], pair_state, newest

    new_rows = enriched[enriched["ts"] > last_processed].copy()
    events: list[dict[str, Any]] = []
    newest_processed = last_processed

    position = int(pair_state.get("position", 0))
    bars_held = int(pair_state.get("bars_held", 0))
    entry_ts = str(pair_state.get("entry_ts", ""))
    entry_price = pair_state.get("entry_price")

    for _, row in new_rows.iterrows():
        ts = row["ts"]
        desired = int(row["delayed_signal"])
        close = float(row["c"])
        newest_processed = ts

        if position != 0:
            bars_held += 1

        event_type = ""
        old_position = position

        if position == 0 and desired != 0:
            position = desired
            bars_held = 0
            entry_ts = ts.isoformat()
            entry_price = close
            event_type = "entry"

        elif position != 0 and desired == 0 and bars_held >= MIN_HOLD_BARS:
            position = 0
            event_type = "exit"

        elif (
            position != 0
            and desired == -position
            and bars_held >= MIN_HOLD_BARS
        ):
            position = desired
            bars_held = 0
            entry_ts = ts.isoformat()
            entry_price = close
            event_type = "reversal"

        if event_type:
            events.append(
                {
                    "cycle_id": cycle_id,
                    "provider": "twelve_data",
                    "pair": pair,
                    "bar_ts_utc": ts.isoformat(),
                    "event_type": event_type,
                    "old_position": position_name(old_position),
                    "new_position": position_name(position),
                    "desired_delayed_signal": position_name(desired),
                    "close": close,
                    "fast_ma": (
                        None if pd.isna(row["fast_ma"]) else float(row["fast_ma"])
                    ),
                    "slow_ma": (
                        None if pd.isna(row["slow_ma"]) else float(row["slow_ma"])
                    ),
                    "volatility": (
                        None if pd.isna(row["vol"]) else float(row["vol"])
                    ),
                    "volatility_ok": bool(row["vol_ok"]),
                    "in_session": bool(row["in_session"]),
                    "bars_held_after": bars_held,
                    "entry_ts_after": entry_ts,
                    "entry_price_after": entry_price,
                    "observation_only": True,
                }
            )

    pair_state.update(
        {
            "position": position,
            "bars_held": bars_held,
            "entry_ts": entry_ts,
            "entry_price": entry_price,
            "last_observed_signal": (
                int(new_rows["delayed_signal"].iloc[-1])
                if not new_rows.empty
                else pair_state.get("last_observed_signal", 0)
            ),
        }
    )
    return events, pair_state, newest_processed

# --- KQTRL M006b.1 GAP PROTECTION BEGIN ---
_M006B1_MAX_IN_SESSION_BARS = 4

def _m006b1_position_is_flat(pair_state):
    p = pair_state.get("position", 0) if isinstance(pair_state, dict) else 0
    return p in (0, "0", None, "", "flat", "FLAT")

def _m006b1_count_pending_session_bars(pair, last_processed, newest):
    import pandas as _pd
    if last_processed is None or newest is None:
        return 0
    lp = _pd.Timestamp(last_processed)
    nw = _pd.Timestamp(newest)
    if lp.tzinfo is None:
        lp = lp.tz_localize("UTC")
    else:
        lp = lp.tz_convert("UTC")
    if nw.tzinfo is None:
        nw = nw.tz_localize("UTC")
    else:
        nw = nw.tz_convert("UTC")
    if nw <= lp:
        return 0
    start, end = session_hours(pair)
    idx = _pd.date_range(lp + _pd.Timedelta(minutes=5), nw, freq="5min", tz="UTC")
    if len(idx) == 0:
        return 0
    mask = (idx.dayofweek < 5) & (idx.hour >= int(start)) & (idx.hour < int(end))
    return int(mask.sum())

def process_pair(pair, bars, pair_state, last_processed, cycle_id):
    if last_processed is not None and bars is not None and len(bars):
        _ts_col = "ts" if "ts" in bars.columns else ("timestamp" if "timestamp" in bars.columns else None)
        if _ts_col is not None:
            _newest = bars[_ts_col].iloc[-1]
            _pending = _m006b1_count_pending_session_bars(pair, last_processed, _newest)
            if _pending > _M006B1_MAX_IN_SESSION_BARS:
                if not _m006b1_position_is_flat(pair_state):
                    raise RuntimeError(
                        f"M006b.1 FAIL-CLOSED {pair}: {_pending} pending in-session bars "
                        f"after watermark {last_processed}, but position is not flat. "
                        f"Historical replay blocked pending manual review."
                    )
                print(
                    f"M006b.1 NON_PROSPECTIVE GAP QUARANTINE {pair}: "
                    f"{_pending} pending in-session bars after {last_processed}; "
                    f"advancing prospective boundary to {_newest} without replay."
                )
                if isinstance(pair_state, dict):
                    pair_state["m006b1_gap_quarantine"] = {
                        "cycle_id": str(cycle_id),
                        "previous_watermark": str(last_processed),
                        "new_boundary": str(_newest),
                        "pending_in_session_bars": int(_pending),
                        "classification": "NON_PROSPECTIVE",
                    }
                return _process_pair_original(pair, bars, pair_state, None, cycle_id)
    return _process_pair_original(pair, bars, pair_state, last_processed, cycle_id)
# --- KQTRL M006b.1 GAP PROTECTION END ---



def append_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bars-dir", required=True)
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--cycle-id", required=True)
    args = parser.parse_args()

    bars_dir = Path(args.bars_dir)
    candidate_dir = Path(args.candidate_dir)
    metadata_dir = candidate_dir / "metadata"
    events_dir = candidate_dir / "events"
    reports_dir = candidate_dir / "reports"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    events_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    state_path = metadata_dir / "twelve_shadow_state.json"
    watermark_path = metadata_dir / "twelve_shadow_watermark.json"

    state = load_json(
        state_path,
        {
            "provider": "twelve_data",
            "observation_only": True,
            "pairs": {},
        },
    )
    watermark = load_json(watermark_path, {"latest_by_pair": {}})

    all_events: list[dict[str, Any]] = []
    latest_by_pair: dict[str, str] = dict(watermark.get("latest_by_pair", {}))
    first_cycle_pairs: list[str] = []

    for pair in PAIRS:
        bars = load_bars(bars_dir / f"{pair}_5m.csv")
        last_text = latest_by_pair.get(pair)
        last_processed = pd.Timestamp(last_text) if last_text else None

        pair_state = dict(state.get("pairs", {}).get(pair, {}))
        events, pair_state, newest = process_pair(
            pair,
            bars,
            pair_state,
            last_processed,
            args.cycle_id,
        )

        if last_processed is None:
            first_cycle_pairs.append(pair)

        state.setdefault("pairs", {})[pair] = pair_state
        if newest is not None:
            latest_by_pair[pair] = newest.isoformat()
        all_events.extend(events)

    state["updated_at_utc"] = pd.Timestamp.now(tz="UTC").isoformat()
    state["last_cycle_id"] = args.cycle_id
    watermark_payload = {
        "provider": "twelve_data",
        "observation_only": True,
        "updated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "latest_by_pair": latest_by_pair,
    }

    atomic_json(state_path, state)
    atomic_json(watermark_path, watermark_payload)

    daily_path = events_dir / (
        "twelve_shadow_events_"
        + pd.Timestamp.now(tz="UTC").strftime("%Y%m%d")
        + ".csv"
    )
    append_csv(daily_path, all_events)

    cycle_audit_path = events_dir / f"cycle_{args.cycle_id}.csv"
    if all_events:
        pd.DataFrame(all_events).to_csv(cycle_audit_path, index=False)
    else:
        pd.DataFrame(
            columns=[
                "cycle_id",
                "provider",
                "pair",
                "bar_ts_utc",
                "event_type",
                "old_position",
                "new_position",
                "observation_only",
            ]
        ).to_csv(cycle_audit_path, index=False)

    summary = {
        "cycle_id": args.cycle_id,
        "observation_only": True,
        "first_cycle_boundary_pairs": first_cycle_pairs,
        "events_generated": len(all_events),
        "entries": sum(e["event_type"] == "entry" for e in all_events),
        "exits": sum(e["event_type"] == "exit" for e in all_events),
        "reversals": sum(e["event_type"] == "reversal" for e in all_events),
        "latest_by_pair": latest_by_pair,
        "canonical_m005_modified": False,
    }
    summary_path = reports_dir / f"cycle_summary_{args.cycle_id}.json"
    atomic_json(summary_path, summary)

    print("KQTRL M005 v1.2f — TWELVE DATA SHADOW CANDIDATE")
    print("=" * 72)
    print(f"Cycle: {args.cycle_id}")
    print("Mode: OBSERVATION ONLY")
    if first_cycle_pairs:
        print(
            "Prospective boundary established for: "
            + ", ".join(first_cycle_pairs)
        )
        print("No historical signals were reconstructed for those pairs.")
    print(f"Events generated: {len(all_events)}")
    print(f"Entries: {summary['entries']}")
    print(f"Exits: {summary['exits']}")
    print(f"Reversals: {summary['reversals']}")
    print("Canonical M005 modified: False")
    print(f"Cycle audit: {cycle_audit_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

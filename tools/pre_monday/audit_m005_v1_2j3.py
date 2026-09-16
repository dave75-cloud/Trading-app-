#!/usr/bin/env python3
"""
KQTRL M005 v1.2j.3 — Full Behavioural Equivalence Audit

Purpose
-------
Compare the ACTUAL Twelve shadow observer `process_pair()` implementation against
an independent reference implementation of the frozen M005/M006b.1 rules.

This audit:
- imports and executes the actual observer;
- independently recomputes MA20/MA50, return-volatility window 12 with ddof=0,
  weekday/session eligibility, raw signal and one-bar delayed signal;
- independently implements entry / exit / reversal / min-hold state transitions;
- independently implements M006b.1 gap quarantine (>4 pending in-session M5 bars);
- tests natural sequential behaviour on the local Twelve stores;
- tests first-cycle boundary establishment;
- tests flat-position gap quarantine;
- tests non-flat gap fail-closed behaviour;
- compares events, state and watermark;
- never writes canonical M005 files.

A PASS here is materially stronger than the superseded v1.2j audit because the
reference path never calls the actual observer's indicator or state-machine helpers.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDJPY")
FAST = 20
SLOW = 50
VOL_WINDOW = 12
VOL_THRESHOLD = 0.0005
MIN_HOLD_BARS = 3
MAX_PENDING_IN_SESSION_BARS = 4
SESSIONS = {
    "AUDUSD": (11, 14),
    "EURUSD": (11, 13),
    "GBPUSD": (11, 13),
    "USDJPY": (11, 13),
}

STATE_KEYS = (
    "position",
    "bars_held",
    "entry_ts",
    "entry_price",
    "last_observed_signal",
    "m006b1_gap_quarantine",
)

EVENT_KEYS = (
    "cycle_id",
    "provider",
    "pair",
    "bar_ts_utc",
    "event_type",
    "old_position",
    "new_position",
    "desired_delayed_signal",
    "close",
    "fast_ma",
    "slow_ma",
    "volatility",
    "volatility_ok",
    "in_session",
    "bars_held_after",
    "entry_ts_after",
    "entry_price_after",
    "observation_only",
)


def load_actual(path: Path):
    spec = importlib.util.spec_from_file_location("kqtrl_actual_observer", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm_bars(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    if "ts" not in x.columns and "timestamp" in x.columns:
        x = x.rename(columns={"timestamp": "ts"})
    x["ts"] = pd.to_datetime(x["ts"], utc=True, errors="raise")
    x = x.sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)
    return x


def pos_name(v: int) -> str:
    return {1: "long", -1: "short", 0: "flat"}[int(v)]


def ref_add_indicators(df: pd.DataFrame, pair: str) -> pd.DataFrame:
    x = norm_bars(df)
    x["ret"] = x["c"].pct_change()
    x["fast_ma"] = x["c"].rolling(FAST, min_periods=FAST).mean()
    x["slow_ma"] = x["c"].rolling(SLOW, min_periods=SLOW).mean()
    x["vol"] = (
        x["ret"]
        .rolling(VOL_WINDOW, min_periods=VOL_WINDOW)
        .std(ddof=0)
    )
    start, end = SESSIONS[pair]
    x["in_session"] = (
        (x["ts"].dt.hour >= start)
        & (x["ts"].dt.hour < end)
        & (x["ts"].dt.dayofweek < 5)
    )
    x["vol_ok"] = x["vol"] >= VOL_THRESHOLD
    ready = x["fast_ma"].notna() & x["slow_ma"].notna() & x["vol"].notna()
    x["raw_signal"] = 0
    x.loc[
        ready & x["in_session"] & x["vol_ok"] & (x["fast_ma"] > x["slow_ma"]),
        "raw_signal",
    ] = 1
    x.loc[
        ready & x["in_session"] & x["vol_ok"] & (x["fast_ma"] < x["slow_ma"]),
        "raw_signal",
    ] = -1
    x["delayed_signal"] = x["raw_signal"].shift(1).fillna(0).astype(int)
    return x


def count_pending_session_bars(pair: str, last_processed, newest) -> int:
    if last_processed is None or newest is None:
        return 0
    lp = pd.Timestamp(last_processed)
    nw = pd.Timestamp(newest)
    lp = lp.tz_localize("UTC") if lp.tzinfo is None else lp.tz_convert("UTC")
    nw = nw.tz_localize("UTC") if nw.tzinfo is None else nw.tz_convert("UTC")
    if nw <= lp:
        return 0
    start, end = SESSIONS[pair]
    idx = pd.date_range(lp + pd.Timedelta(minutes=5), nw, freq="5min", tz="UTC")
    if len(idx) == 0:
        return 0
    mask = (idx.dayofweek < 5) & (idx.hour >= start) & (idx.hour < end)
    return int(mask.sum())


def flat_state(state: dict[str, Any]) -> bool:
    p = state.get("position", 0) if isinstance(state, dict) else 0
    return p in (0, "0", None, "", "flat", "FLAT")


class RefGapError(RuntimeError):
    pass


def ref_original(
    pair: str,
    bars: pd.DataFrame,
    pair_state: dict[str, Any],
    last_processed,
    cycle_id: str,
):
    enriched = ref_add_indicators(bars, pair)

    if last_processed is None:
        newest = enriched["ts"].max()
        pair_state.setdefault("position", 0)
        pair_state.setdefault("bars_held", 0)
        pair_state.setdefault("entry_ts", "")
        pair_state.setdefault("entry_price", None)
        pair_state["last_observed_signal"] = int(
            enriched.loc[enriched["ts"] == newest, "delayed_signal"].iloc[-1]
        )
        return [], pair_state, newest

    lp = pd.Timestamp(last_processed)
    new_rows = enriched[enriched["ts"] > lp].copy()
    events: list[dict[str, Any]] = []
    newest_processed = lp

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

        elif position != 0 and desired == -position and bars_held >= MIN_HOLD_BARS:
            position = desired
            bars_held = 0
            entry_ts = ts.isoformat()
            entry_price = close
            event_type = "reversal"

        if event_type:
            events.append({
                "cycle_id": cycle_id,
                "provider": "twelve_data",
                "pair": pair,
                "bar_ts_utc": ts.isoformat(),
                "event_type": event_type,
                "old_position": pos_name(old_position),
                "new_position": pos_name(position),
                "desired_delayed_signal": pos_name(desired),
                "close": close,
                "fast_ma": None if pd.isna(row["fast_ma"]) else float(row["fast_ma"]),
                "slow_ma": None if pd.isna(row["slow_ma"]) else float(row["slow_ma"]),
                "volatility": None if pd.isna(row["vol"]) else float(row["vol"]),
                "volatility_ok": bool(row["vol_ok"]),
                "in_session": bool(row["in_session"]),
                "bars_held_after": bars_held,
                "entry_ts_after": entry_ts,
                "entry_price_after": entry_price,
                "observation_only": True,
            })

    pair_state.update({
        "position": position,
        "bars_held": bars_held,
        "entry_ts": entry_ts,
        "entry_price": entry_price,
        "last_observed_signal": (
            int(new_rows["delayed_signal"].iloc[-1])
            if not new_rows.empty
            else pair_state.get("last_observed_signal", 0)
        ),
    })
    return events, pair_state, newest_processed


def ref_process(
    pair: str,
    bars: pd.DataFrame,
    pair_state: dict[str, Any],
    last_processed,
    cycle_id: str,
):
    if last_processed is not None and bars is not None and len(bars):
        ts_col = "ts" if "ts" in bars.columns else (
            "timestamp" if "timestamp" in bars.columns else None
        )
        if ts_col is not None:
            newest = bars[ts_col].iloc[-1]
            pending = count_pending_session_bars(pair, last_processed, newest)
            if pending > MAX_PENDING_IN_SESSION_BARS:
                if not flat_state(pair_state):
                    raise RefGapError(
                        f"gap fail-closed {pair}: {pending} pending in-session bars"
                    )
                if isinstance(pair_state, dict):
                    pair_state["m006b1_gap_quarantine"] = {
                        "cycle_id": str(cycle_id),
                        "previous_watermark": str(last_processed),
                        "new_boundary": str(newest),
                        "pending_in_session_bars": int(pending),
                        "classification": "NON_PROSPECTIVE",
                    }
                return ref_original(pair, bars, pair_state, None, cycle_id)
    return ref_original(pair, bars, pair_state, last_processed, cycle_id)


def same_num(a, b, tol=1e-12):
    if a is None and b is None:
        return True
    try:
        if pd.isna(a) and pd.isna(b):
            return True
    except Exception:
        pass
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)
    return a == b


def compare_events(actual, ref):
    if len(actual) != len(ref):
        return False, f"event count actual={len(actual)} ref={len(ref)}"
    for i, (a, r) in enumerate(zip(actual, ref)):
        for k in EVENT_KEYS:
            if not same_num(a.get(k), r.get(k)):
                return False, f"event[{i}] {k}: actual={a.get(k)!r} ref={r.get(k)!r}"
    return True, ""


def compare_states(actual, ref):
    keys = set(actual) | set(ref)
    keys = keys.intersection(STATE_KEYS)
    for k in sorted(keys):
        av, rv = actual.get(k), ref.get(k)
        if k == "m006b1_gap_quarantine":
            if (av or None) != (rv or None):
                return False, f"state {k}: actual={av!r} ref={rv!r}"
        elif not same_num(av, rv):
            return False, f"state {k}: actual={av!r} ref={rv!r}"
    return True, ""


def compare_watermark(a, r):
    if a is None or r is None:
        return a is None and r is None
    return pd.Timestamp(a) == pd.Timestamp(r)


def run_sequential(mod, pair, bars, warmup=80, chunk=3):
    if len(bars) <= warmup + 1:
        return 0, 0, "insufficient bars"
    astate, rstate = {}, {}
    cycle = f"AUDIT_{pair}_INIT"
    prefix = bars.iloc[:warmup].copy()
    ae, astate, aw = mod.process_pair(pair, prefix.copy(), astate, None, cycle)
    re, rstate, rw = ref_process(pair, prefix.copy(), rstate, None, cycle)
    ok, why = compare_events(ae, re)
    if not ok or not compare_watermark(aw, rw):
        return 0, 1, f"initial boundary mismatch: {why}"
    ok, why = compare_states(astate, rstate)
    if not ok:
        return 0, 1, f"initial state mismatch: {why}"

    calls = 1
    events_seen = 0
    cursor = warmup
    while cursor < len(bars):
        end = min(cursor + chunk, len(bars))
        prefix = bars.iloc[:end].copy()
        cycle = f"AUDIT_{pair}_{end}"
        ae, astate, aw = mod.process_pair(
            pair, prefix.copy(), copy.deepcopy(astate), aw, cycle
        )
        re, rstate, rw = ref_process(
            pair, prefix.copy(), copy.deepcopy(rstate), rw, cycle
        )
        calls += 1
        events_seen += len(ae)

        ok, why = compare_events(ae, re)
        if not ok:
            return calls, events_seen, f"event mismatch at cursor {end}: {why}"
        ok, why = compare_states(astate, rstate)
        if not ok:
            return calls, events_seen, f"state mismatch at cursor {end}: {why}"
        if not compare_watermark(aw, rw):
            return calls, events_seen, (
                f"watermark mismatch at cursor {end}: actual={aw} ref={rw}"
            )
        cursor = end
    return calls, events_seen, ""


def find_gap_window(pair, bars, min_pending=5):
    ts = list(bars["ts"])
    for j in range(1, len(ts)):
        for i in range(max(0, j - 20), j):
            if count_pending_session_bars(pair, ts[i], ts[j]) >= min_pending:
                return i, j
    return None


def run_gap_tests(mod, pair, bars):
    win = find_gap_window(pair, bars, 5)
    if not win:
        return False, "could not find >=5 pending in-session-bar window"
    i, j = win
    prefix = bars.iloc[:j+1].copy()
    lp = bars.iloc[i]["ts"]
    cycle = f"AUDIT_GAP_{pair}"

    # Flat gap: must quarantine and advance without replay.
    astate = {"position": 0, "bars_held": 0, "entry_ts": "", "entry_price": None}
    rstate = copy.deepcopy(astate)
    ae, ast, aw = mod.process_pair(pair, prefix.copy(), copy.deepcopy(astate), lp, cycle)
    re, rst, rw = ref_process(pair, prefix.copy(), copy.deepcopy(rstate), lp, cycle)
    ok, why = compare_events(ae, re)
    if not ok:
        return False, f"flat gap event mismatch: {why}"
    ok, why = compare_states(ast, rst)
    if not ok:
        return False, f"flat gap state mismatch: {why}"
    if not compare_watermark(aw, rw):
        return False, f"flat gap watermark mismatch actual={aw} ref={rw}"

    # Non-flat gap: both must fail closed.
    aerr = rerr = None
    nf = {
        "position": 1, "bars_held": 1,
        "entry_ts": pd.Timestamp(lp).isoformat(),
        "entry_price": float(bars.iloc[i]["c"]),
    }
    try:
        mod.process_pair(pair, prefix.copy(), copy.deepcopy(nf), lp, cycle+"_NF")
    except RuntimeError as e:
        aerr = e
    try:
        ref_process(pair, prefix.copy(), copy.deepcopy(nf), lp, cycle+"_NF")
    except RefGapError as e:
        rerr = e
    if aerr is None or rerr is None:
        return False, (
            f"non-flat gap fail-closed mismatch actual_error={aerr is not None} "
            f"ref_error={rerr is not None}"
        )
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=str(Path.home()/"Projects"/"Trading-app-"))
    ap.add_argument("--observer", default="cli/run_m005_twelve_shadow_observer.py")
    ap.add_argument("--bars-dir", default="data/live_5m_twelve")
    ap.add_argument("--rows", type=int, default=2000)
    ap.add_argument("--chunk", type=int, default=3)
    args = ap.parse_args()

    project = Path(args.project).expanduser().resolve()
    observer = project / args.observer
    mod = load_actual(observer)

    print("KQTRL M005 v1.2j.3 — FULL BEHAVIOURAL EQUIVALENCE AUDIT")
    print("=" * 82)
    print("Actual observer:", observer)
    print("SHA256:", hashlib.sha256(observer.read_bytes()).hexdigest())
    print("Reference: independent implementation (does not call actual helpers)")
    print("Canonical writes: NONE")
    print()

    failures = []
    total_calls = total_events = 0

    for pair in PAIRS:
        path = project / args.bars_dir / f"{pair}_5m.csv"
        if not path.exists():
            failures.append(f"{pair}: missing bars {path}")
            continue
        bars = norm_bars(pd.read_csv(path).tail(args.rows))
        calls, events, err = run_sequential(
            mod, pair, bars, warmup=max(SLOW + VOL_WINDOW + 5, 80), chunk=args.chunk
        )
        total_calls += calls
        total_events += events
        if err:
            print(f"{pair}: SEQUENTIAL FAIL — {err}")
            failures.append(f"{pair} sequential: {err}")
            continue

        gok, gwhy = run_gap_tests(mod, pair, bars)
        if not gok:
            print(f"{pair}: GAP TEST FAIL — {gwhy}")
            failures.append(f"{pair} gap: {gwhy}")
            continue

        print(
            f"{pair}: PASS sequential_calls={calls} natural_events={events} "
            f"first_boundary=PASS flat_gap_quarantine=PASS nonflat_gap_failclosed=PASS"
        )

    print("-" * 82)
    print("Total actual/reference sequential calls:", total_calls)
    print("Natural actual events compared:", total_events)

    if failures:
        print("FULL_BEHAVIOURAL_AUDIT: FAIL")
        for f in failures:
            print(" -", f)
        print("Canonical M005 modified: False")
        return 10

    print("FULL_BEHAVIOURAL_AUDIT: PASS")
    print("Actual process_pair matched the independent reference on:")
    print("  first-cycle prospective boundary; entries; exits; reversals;")
    print("  one-bar delayed signal; 3-bar minimum hold; state/watermark evolution;")
    print("  M006b.1 flat-gap NON_PROSPECTIVE quarantine;")
    print("  M006b.1 non-flat gap fail-closed protection.")
    print("Canonical M005 modified: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

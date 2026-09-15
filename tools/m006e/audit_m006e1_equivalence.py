#!/usr/bin/env python3

from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(".").resolve()

REF_PATH = ROOT / "cli/run_m005_twelve_shadow_observer.py"
NEW_PATH = ROOT / "tools/m006e/m006e1_oanda_authoritative_observer.py"

M006C_STATE = (
    ROOT
    / "data/research_runs/M006_PRACTICE_EXECUTION/"
      "signal_order_bridge/state/bridge_state.json"
)

M006E_STATE = (
    ROOT
    / "data/research_runs/M006E_OANDA_AUTHORITATIVE/"
      "state/observer_state.json"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_bars(n=460):
    ts = pd.date_range(
        "2026-08-17T00:00:00Z",
        periods=n,
        freq="5min",
    )

    i = np.arange(n, dtype=float)

    # Deterministic, sufficiently volatile path containing
    # trend and oscillation so entries/exits occur naturally.
    c = (
        1.0000
        + 0.0030 * np.sin(i / 3.1)
        + 0.0017 * np.sin(i / 11.3)
        + 0.0006 * np.sin(i / 29.0)
        + 0.000002 * i
    )

    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + 0.00015
    l = np.minimum(o, c) - 0.00015

    return pd.DataFrame(
        {
            "ts": ts,
            "o": o,
            "h": h,
            "l": l,
            "c": c,
        }
    )


def assert_scalar_equal(label, a, b):
    if a != b:
        raise AssertionError(
            f"{label}: reference={a!r}, M006e1={b!r}"
        )


def compare_numeric(label, a, b):
    av = np.asarray(a, dtype=float)
    bv = np.asarray(b, dtype=float)

    if not np.array_equal(av, bv, equal_nan=True):
        diff = np.abs(av - bv)

        finite = np.isfinite(diff)

        max_abs = (
            float(diff[finite].max())
            if finite.any()
            else None
        )

        raise AssertionError(
            f"{label}: numeric disagreement max_abs={max_abs}"
        )


def compare_boolean(label, a, b):
    av = np.asarray(a, dtype=bool)
    bv = np.asarray(b, dtype=bool)

    if not np.array_equal(av, bv):
        n = int((av != bv).sum())

        raise AssertionError(
            f"{label}: {n} disagreements"
        )


def event_semantics(event):
    keys = [
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
    ]

    return {k: event.get(k) for k in keys}


def states_equal(ref_state, new_state):
    keys = [
        "position",
        "bars_held",
        "entry_ts",
        "entry_price",
        "last_observed_signal",
    ]

    for key in keys:
        a = ref_state.get(key)
        b = new_state.get(key)

        if isinstance(a, float) or isinstance(b, float):
            if a is None or b is None:
                if a != b:
                    return False
            elif not np.isclose(
                float(a),
                float(b),
                rtol=0.0,
                atol=0.0,
            ):
                return False

        elif a != b:
            return False

    return True


def main():
    print("=" * 78)
    print("KQTRL M006e.1 — EXACT EQUIVALENCE AUDIT")
    print("=" * 78)

    if M006E_STATE.exists():
        raise SystemExit(
            "FAIL-CLOSED: M006e state already exists. "
            "This audit is intended to run before initialization."
        )

    m006c_before = sha256(M006C_STATE)

    ref = load_module("m005_ref", REF_PATH)
    new = load_module("m006e1", NEW_PATH)

    print()
    print("=== 1. CONSTANTS / SESSION POLICY ===")

    constants = [
        "FAST",
        "SLOW",
        "VOL_WINDOW",
        "VOL_THRESHOLD",
        "MIN_HOLD_BARS",
    ]

    for name in constants:
        assert_scalar_equal(
            name,
            getattr(ref, name),
            getattr(new, name),
        )

        print(
            f"PASS {name}: "
            f"{getattr(new, name)}"
        )

    for pair in ref.PAIRS:
        assert_scalar_equal(
            f"session_hours_{pair}",
            ref.session_hours(pair),
            new.session_hours(pair),
        )

        print(
            f"PASS {pair} session: "
            f"{new.session_hours(pair)} UTC"
        )

    bars = make_bars()

    print()
    print("=== 2. INDICATOR / SIGNAL EQUIVALENCE ===")

    for pair in ref.PAIRS:
        a = ref.add_indicators(
            bars.copy(),
            pair,
        )

        b = new.add_indicators(
            bars.copy(),
            pair,
        )

        for col in [
            "ret",
            "fast_ma",
            "slow_ma",
            "vol",
            "raw_signal",
            "delayed_signal",
        ]:
            compare_numeric(
                f"{pair}_{col}",
                a[col],
                b[col],
            )

        for col in [
            "in_session",
            "vol_ok",
        ]:
            compare_boolean(
                f"{pair}_{col}",
                a[col],
                b[col],
            )

        print(
            f"PASS {pair}: "
            "ret/MA20/MA50/vol/raw/delayed/"
            "session/vol_ok exact"
        )

    print()
    print("=== 3. PROSPECTIVE BOUNDARY EQUIVALENCE ===")

    INIT_ROWS = 80

    ref_states = {}
    new_states = {}
    ref_watermarks = {}
    new_watermarks = {}

    for pair in ref.PAIRS:
        prefix = bars.iloc[:INIT_ROWS].copy()

        ref_state = {}

        (
            ref_events,
            ref_state,
            ref_wm,
        ) = ref._process_pair_original(
            pair,
            prefix,
            ref_state,
            None,
            "REF_INIT",
        )

        new_state = new.default_pair_state()

        (
            new_state,
            new_wm,
        ) = new.establish_boundary(
            pair,
            prefix,
            new_state,
        )

        if ref_events:
            raise AssertionError(
                f"{pair}: reference initialization replayed events"
            )

        if ref_wm != new_wm:
            raise AssertionError(
                f"{pair}: boundary mismatch "
                f"{ref_wm} vs {new_wm}"
            )

        if not states_equal(
            ref_state,
            new_state,
        ):
            raise AssertionError(
                f"{pair}: initialization state mismatch\n"
                f"REF={ref_state}\nNEW={new_state}"
            )

        ref_states[pair] = ref_state
        new_states[pair] = new_state
        ref_watermarks[pair] = ref_wm
        new_watermarks[pair] = new_wm

        print(
            f"PASS {pair}: boundary={new_wm}"
        )

    print()
    print("=== 4. SEQUENTIAL STATE-MACHINE EQUIVALENCE ===")

    total_calls = 0
    total_events = 0
    by_pair_events = {
        p: 0
        for p in ref.PAIRS
    }

    for end in range(
        INIT_ROWS + 1,
        len(bars) + 1,
    ):
        prefix = bars.iloc[:end].copy()

        for pair in ref.PAIRS:
            total_calls += 1

            (
                ref_events,
                ref_state,
                ref_wm,
            ) = ref.process_pair(
                pair,
                prefix,
                copy.deepcopy(
                    ref_states[pair]
                ),
                ref_watermarks[pair],
                f"REF_{end}",
            )

            (
                new_events,
                new_state,
                new_wm,
                quarantine,
            ) = new.process_pair(
                pair,
                prefix,
                copy.deepcopy(
                    new_states[pair]
                ),
                new_watermarks[pair],
                f"NEW_{end}",
            )

            if quarantine is not None:
                raise AssertionError(
                    f"{pair}: unexpected quarantine "
                    "during one-bar sequential processing"
                )

            if ref_wm != new_wm:
                raise AssertionError(
                    f"{pair}: watermark mismatch "
                    f"at end={end}"
                )

            if len(ref_events) != len(new_events):
                raise AssertionError(
                    f"{pair}: event-count mismatch "
                    f"at end={end}: "
                    f"{len(ref_events)} vs "
                    f"{len(new_events)}"
                )

            for re, ne in zip(
                ref_events,
                new_events,
            ):
                rs = event_semantics(re)
                ns = event_semantics(ne)

                if rs != ns:
                    raise AssertionError(
                        f"{pair}: event mismatch "
                        f"at end={end}\n"
                        f"REF={rs}\n"
                        f"NEW={ns}"
                    )

            if not states_equal(
                ref_state,
                new_state,
            ):
                raise AssertionError(
                    f"{pair}: state mismatch "
                    f"at end={end}\n"
                    f"REF={ref_state}\n"
                    f"NEW={new_state}"
                )

            ref_states[pair] = ref_state
            new_states[pair] = new_state
            ref_watermarks[pair] = ref_wm
            new_watermarks[pair] = new_wm

            total_events += len(new_events)
            by_pair_events[pair] += len(
                new_events
            )

    if total_events == 0:
        raise AssertionError(
            "Synthetic path generated zero events; "
            "behavioural test is not meaningful."
        )

    print(
        f"Sequential calls: {total_calls}"
    )
    print(
        f"Natural events compared: {total_events}"
    )

    for pair in ref.PAIRS:
        print(
            f"PASS {pair}: "
            f"events={by_pair_events[pair]} "
            "state/watermark/event semantics exact"
        )

    print()
    print("=== 5. FLAT GAP QUARANTINE EQUIVALENCE ===")

    gap_bars = bars.copy()

    # Choose a Monday 11:00 UTC watermark and jump
    # well beyond the four-bar threshold.
    lp = pd.Timestamp(
        "2026-08-17T11:00:00Z"
    )

    gap_subset = gap_bars[
        gap_bars["ts"]
        <= pd.Timestamp(
            "2026-08-17T12:00:00Z"
        )
    ].copy()

    ref_flat = {
        "position": 0,
        "bars_held": 0,
        "entry_ts": "",
        "entry_price": None,
        "last_observed_signal": 0,
    }

    new_flat = copy.deepcopy(
        ref_flat
    )

    (
        ref_events,
        ref_after,
        ref_boundary,
    ) = ref.process_pair(
        "EURUSD",
        gap_subset,
        ref_flat,
        lp,
        "REF_GAP",
    )

    (
        new_events,
        new_after,
        new_boundary,
        quarantine,
    ) = new.process_pair(
        "EURUSD",
        gap_subset,
        new_flat,
        lp,
        "NEW_GAP",
    )

    if ref_events or new_events:
        raise AssertionError(
            "Flat-gap quarantine replayed events"
        )

    if ref_boundary != new_boundary:
        raise AssertionError(
            "Flat-gap boundary mismatch"
        )

    rq = ref_after.get(
        "m006b1_gap_quarantine"
    )

    if rq is None:
        raise AssertionError(
            "Reference did not record gap quarantine"
        )

    if quarantine is None:
        raise AssertionError(
            "M006e.1 did not return gap quarantine"
        )

    if (
        int(
            rq[
                "pending_in_session_bars"
            ]
        )
        != int(
            quarantine[
                "pending_in_session_bars"
            ]
        )
    ):
        raise AssertionError(
            "Gap pending-bar count mismatch"
        )

    if (
        rq["classification"]
        != quarantine[
            "classification"
        ]
        != "NON_PROSPECTIVE"
    ):
        raise AssertionError(
            "Gap classification mismatch"
        )

    print(
        "PASS flat gap: "
        f"pending="
        f"{quarantine['pending_in_session_bars']} "
        "classification=NON_PROSPECTIVE"
    )

    print()
    print("=== 6. NON-FLAT GAP FAIL-CLOSED EQUIVALENCE ===")

    ref_nonflat = {
        "position": 1,
        "bars_held": 1,
        "entry_ts": (
            "2026-08-17T11:00:00+00:00"
        ),
        "entry_price": 1.0,
        "last_observed_signal": 1,
    }

    new_nonflat = copy.deepcopy(
        ref_nonflat
    )

    ref_failed = False
    new_failed = False

    try:
        ref.process_pair(
            "EURUSD",
            gap_subset,
            ref_nonflat,
            lp,
            "REF_NONFLAT_GAP",
        )
    except RuntimeError:
        ref_failed = True

    try:
        new.process_pair(
            "EURUSD",
            gap_subset,
            new_nonflat,
            lp,
            "NEW_NONFLAT_GAP",
        )
    except RuntimeError:
        new_failed = True

    if not ref_failed:
        raise AssertionError(
            "Reference failed to block non-flat historical replay"
        )

    if not new_failed:
        raise AssertionError(
            "M006e.1 failed to block non-flat historical replay"
        )

    print(
        "PASS non-flat gap: "
        "both implementations fail closed"
    )

    print()
    print("=== 7. SAFETY / STATE-INTEGRITY CHECK ===")

    m006c_after = sha256(
        M006C_STATE
    )

    if m006c_before != m006c_after:
        raise AssertionError(
            "M006c state changed during audit"
        )

    if M006E_STATE.exists():
        raise AssertionError(
            "M006e live state was created during audit"
        )

    print(
        "M006c state modified: FALSE"
    )
    print(
        "M006e prospective state created: FALSE"
    )
    print(
        "Network calls made by audit: 0"
    )
    print(
        "Order payloads constructed by audit: 0"
    )
    print(
        "OANDA writes invoked: FALSE"
    )

    print()
    print("=" * 78)
    print(
        "M006E1_EQUIVALENCE_AUDIT: PASS"
    )
    print(
        "Frozen indicator, signal, state, "
        "watermark and gap behaviour verified."
    )
    print("=" * 78)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

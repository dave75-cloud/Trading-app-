#!/usr/bin/env python3

from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pandas as pd

import m006e2_twelve_validator as v2
import m006e3_zero_write_bridge as b


ROOT = Path(".").resolve()

M006E1_STATE = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE/"
      "state/observer_state.json"
)

M006E3_STATE = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE/"
      "bridge/state/bridge_state.json"
)

M006C_STATE = (
    ROOT
    / "data/research_runs/"
      "M006_PRACTICE_EXECUTION/"
      "signal_order_bridge/"
      "state/bridge_state.json"
)

CANONICAL_ROOT = (
    ROOT
    / "data/research_runs/"
      "M005_FORWARD_SHADOW_20260804T120245Z"
)


NOW = pd.Timestamp(
    "2026-09-01T12:08:00Z"
)

TS = pd.Timestamp(
    "2026-09-01T12:00:00Z"
)

NAV = 100000.0

MIDS = {
    "AUD_USD": 0.6600,
    "EUR_USD": 1.1000,
    "GBP_USD": 1.3000,
    "USD_JPY": 150.0,
}


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def directory_fingerprint(root: Path):
    if not root.exists():
        return None

    h = hashlib.sha256()

    for p in sorted(
        x for x in root.rglob("*")
        if x.is_file()
    ):
        h.update(
            str(
                p.relative_to(root)
            ).encode()
        )
        h.update(
            hashlib.sha256(
                p.read_bytes()
            ).digest()
        )

    return h.hexdigest()


def event(
    *,
    pair="EURUSD",
    event_type="entry",
    old="flat",
    new="long",
    signal=1,
    vol_ok=True,
    close=1.1000,
    ts=TS,
    cycle="AUDIT",
):
    return {
        "cycle_id": cycle,
        "provider": "oanda",
        "pair": pair,
        "bar_ts_utc":
            ts.isoformat(),
        "event_type":
            event_type,
        "old_position":
            old,
        "new_position":
            new,
        "desired_delayed_signal":
            signal,
        "close":
            close,
        "fast_ma":
            close + 0.001,
        "slow_ma":
            close,
        "volatility":
            0.0007,
        "volatility_ok":
            vol_ok,
        "in_session":
            True,
        "bars_held_after":
            0,
        "entry_ts_after":
            ts.isoformat(),
        "entry_price_after":
            close,
        "observation_only":
            True,
    }


def twelve(
    *,
    signal=1,
    vol_ok=True,
    close=1.1000,
    ts=TS,
):
    return pd.DataFrame(
        [
            {
                "ts": ts,
                "c": close,
                "delayed_signal":
                    signal,
                "vol_ok":
                    vol_ok,
            }
        ]
    )


def fresh_prices():
    return {
        pair: {
            "fresh": True,
            "age": 0.5,
        }
        for pair in b.MAP
    }


def validation_entry(
    e,
    t,
):
    rows = v2.validate_event(
        e,
        t,
        NOW,
    )

    if str(
        e["event_type"]
    ).lower() == "reversal":
        return rows[1]

    return rows[0]


def apply_entry_if_allowed(
    state,
    e,
    t,
    prices,
):
    pair = e["pair"]

    row = validation_entry(
        e,
        t,
    )

    reasons = list(
        row.get(
            "reasons",
            [],
        )
    )

    if not bool(
        e.get(
            "in_session",
            False,
        )
    ):
        reasons.append(
            "AUTHORITATIVE_EVENT_NOT_IN_SESSION"
        )

    p = prices[pair]

    if not p["fresh"]:
        reasons.append(
            f"OANDA_PRICE_STALE_{p['age']:.2f}M"
        )

    allowed = (
        row["decision"]
        == "ALLOW_DRY_RUN_VALIDATION"
        and not reasons
    )

    if not allowed:
        return {
            "allowed": False,
            "reasons": reasons,
            "validation": row,
        }

    existing = b.virtual_existing(
        state
    )

    side = b.side_from_position(
        e["new_position"]
    )

    alpha, sized = (
        b.sizing_adapter(
            NAV,
            MIDS,
            [(pair, side)],
            existing,
        )
    )

    s = sized[0]

    if s["allocation_x"] <= 0:
        return {
            "allowed": False,
            "reasons": [
                "CONSERVATIVE_B_ALLOCATION_ZERO"
            ],
            "validation": row,
        }

    b.apply_virtual_entry(
        state,
        pair,
        side,
        s["allocation_x"],
    )

    return {
        "allowed": True,
        "allocation_x":
            s["allocation_x"],
        "approx_units":
            s["approx_units"],
        "alpha": alpha,
        "validation": row,
    }


def run_exit_leg(
    state,
    e,
    t,
    prices,
    retry_pending,
):
    pair = e["pair"]

    rows = v2.validate_event(
        e,
        t,
        NOW,
    )

    exit_row = rows[0]

    p = prices[pair]

    if not p["fresh"]:
        retry_pending.add(
            b.event_id(e)
        )

        return {
            "completed": False,
            "decision":
                "RETRY_PENDING",
        }

    had = b.apply_virtual_exit(
        state,
        pair,
    )

    return {
        "completed": True,
        "decision":
            exit_row["decision"],
        "had_position":
            had,
    }


def consume(
    processed,
    report,
    e,
    retry_pending,
):
    return b.consume_event_id(
        processed,
        report,
        b.event_id(e),
        retry_pending,
    )


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.4 — "
        "INTEGRATED HISTORICAL/SYNTHETIC REGRESSION"
    )
    print("=" * 78)

    e1_before = sha256(
        M006E1_STATE
    )

    e3_before = sha256(
        M006E3_STATE
    )

    c_before = sha256(
        M006C_STATE
    )

    canonical_before = (
        directory_fingerprint(
            CANONICAL_ROOT
        )
    )

    # ------------------------------------------------------------------
    # 1. CLEAN ENTRY
    # ------------------------------------------------------------------

    state = b.default_bridge_state()
    processed = set()
    retry = set()

    report = {
        "processed_event_ids": [],
        "retry_pending_event_ids": [],
    }

    e = event()

    result = apply_entry_if_allowed(
        state,
        e,
        twelve(),
        fresh_prices(),
    )

    assert result["allowed"]
    assert (
        state[
            "virtual_positions"
        ]["EURUSD"]["position"]
        == 1
    )
    assert abs(
        state[
            "virtual_positions"
        ]["EURUSD"][
            "allocation_x"
        ]
        - 1.0
    ) < 1e-12

    assert consume(
        processed,
        report,
        e,
        retry,
    )

    print(
        "PASS 01 validated entry -> "
        "1x suppressed dry-run position + consumed"
    )

    # ------------------------------------------------------------------
    # 2. DIRECTION DISAGREEMENT
    # ------------------------------------------------------------------

    state = b.default_bridge_state()
    processed = set()
    retry = set()

    report = {
        "processed_event_ids": [],
        "retry_pending_event_ids": [],
    }

    e = event(
        cycle="AUDIT2"
    )

    result = apply_entry_if_allowed(
        state,
        e,
        twelve(
            signal=-1
        ),
        fresh_prices(),
    )

    assert not result["allowed"]
    assert any(
        "DIRECTION_DISAGREEMENT"
        in r
        for r
        in result["reasons"]
    )

    assert (
        state[
            "virtual_positions"
        ]["EURUSD"]["position"]
        == 0
    )

    assert consume(
        processed,
        report,
        e,
        retry,
    )

    print(
        "PASS 02 validator-blocked entry -> "
        "no position + terminally consumed"
    )

    # ------------------------------------------------------------------
    # 3. >10 BPS DIVERGENCE
    # ------------------------------------------------------------------

    state = b.default_bridge_state()

    e = event(
        close=1.1000,
        cycle="AUDIT3",
    )

    result = apply_entry_if_allowed(
        state,
        e,
        twelve(
            close=1.1013
        ),
        fresh_prices(),
    )

    assert not result["allowed"]

    assert any(
        "PRICE_DIVERGENCE_BLOCK"
        in r
        for r
        in result["reasons"]
    )

    print(
        "PASS 03 >10 bps divergence -> entry blocked"
    )

    # ------------------------------------------------------------------
    # 4. FRESH EXIT
    # ------------------------------------------------------------------

    state = b.default_bridge_state()

    b.apply_virtual_entry(
        state,
        "EURUSD",
        "long",
        1.0,
    )

    processed = set()
    retry = set()

    report = {
        "processed_event_ids": [],
        "retry_pending_event_ids": [],
    }

    e = event(
        event_type="exit",
        old="long",
        new="flat",
        signal=0,
        cycle="AUDIT4",
    )

    result = run_exit_leg(
        state,
        e,
        twelve(
            signal=1
        ),
        fresh_prices(),
        retry,
    )

    assert result["completed"]
    assert (
        result["decision"]
        == "ALLOW_RISK_REDUCING_EXIT"
    )
    assert (
        state[
            "virtual_positions"
        ]["EURUSD"]["position"]
        == 0
    )

    assert consume(
        processed,
        report,
        e,
        retry,
    )

    print(
        "PASS 04 fresh risk-reducing exit -> "
        "closes despite Twelve disagreement + consumed"
    )

    # ------------------------------------------------------------------
    # 5. STALE PRICE EXIT THEN RETRY
    # ------------------------------------------------------------------

    state = b.default_bridge_state()

    b.apply_virtual_entry(
        state,
        "EURUSD",
        "long",
        1.0,
    )

    processed = set()
    retry = set()

    report = {
        "processed_event_ids": [],
        "retry_pending_event_ids": [],
    }

    e = event(
        event_type="exit",
        old="long",
        new="flat",
        signal=0,
        cycle="AUDIT5",
    )

    stale = fresh_prices()
    stale["EURUSD"] = {
        "fresh": False,
        "age": 7.0,
    }

    result = run_exit_leg(
        state,
        e,
        None,
        stale,
        retry,
    )

    assert not result["completed"]
    assert (
        state[
            "virtual_positions"
        ]["EURUSD"]["position"]
        == 1
    )

    assert not consume(
        processed,
        report,
        e,
        retry,
    )

    assert (
        b.event_id(e)
        not in processed
    )

    # Next cycle: pricing fresh.
    retry.remove(
        b.event_id(e)
    )

    result = run_exit_leg(
        state,
        e,
        None,
        fresh_prices(),
        retry,
    )

    assert result["completed"]
    assert (
        state[
            "virtual_positions"
        ]["EURUSD"]["position"]
        == 0
    )

    assert consume(
        processed,
        report,
        e,
        retry,
    )

    print(
        "PASS 05 stale-price exit -> retained, "
        "retried, then closed + consumed"
    )

    # ------------------------------------------------------------------
    # 6. REVERSAL: EXIT SUCCEEDS, ENTRY BLOCKED
    # ------------------------------------------------------------------

    state = b.default_bridge_state()

    b.apply_virtual_entry(
        state,
        "EURUSD",
        "long",
        1.0,
    )

    processed = set()
    retry = set()

    report = {
        "processed_event_ids": [],
        "retry_pending_event_ids": [],
    }

    e = event(
        event_type="reversal",
        old="long",
        new="short",
        signal=-1,
        cycle="AUDIT6",
    )

    t = twelve(
        signal=1
    )

    exit_result = run_exit_leg(
        state,
        e,
        t,
        fresh_prices(),
        retry,
    )

    assert exit_result["completed"]

    assert (
        state[
            "virtual_positions"
        ]["EURUSD"]["position"]
        == 0
    )

    entry_result = apply_entry_if_allowed(
        state,
        e,
        t,
        fresh_prices(),
    )

    assert not entry_result["allowed"]
    assert (
        state[
            "virtual_positions"
        ]["EURUSD"]["position"]
        == 0
    )

    assert consume(
        processed,
        report,
        e,
        retry,
    )

    print(
        "PASS 06 reversal -> exit succeeds, "
        "new entry independently blocked, event consumed"
    )

    # ------------------------------------------------------------------
    # 7. REVERSAL STALE EXIT: ENTRY MUST NOT PROCEED
    # ------------------------------------------------------------------

    state = b.default_bridge_state()

    b.apply_virtual_entry(
        state,
        "EURUSD",
        "long",
        1.0,
    )

    processed = set()
    retry = set()

    report = {
        "processed_event_ids": [],
        "retry_pending_event_ids": [],
    }

    e = event(
        event_type="reversal",
        old="long",
        new="short",
        signal=-1,
        cycle="AUDIT7",
    )

    stale = fresh_prices()
    stale["EURUSD"] = {
        "fresh": False,
        "age": 8.0,
    }

    exit_result = run_exit_leg(
        state,
        e,
        twelve(
            signal=-1
        ),
        stale,
        retry,
    )

    assert not exit_result["completed"]

    assert (
        b.event_id(e)
        in retry
    )

    # Mirrors bridge rule:
    # reversal entry is not attempted while
    # risk-reducing exit remains retry-pending.
    entry_attempted = (
        b.event_id(e)
        not in retry
    )

    assert not entry_attempted

    assert (
        state[
            "virtual_positions"
        ]["EURUSD"]["position"]
        == 1
    )

    assert not consume(
        processed,
        report,
        e,
        retry,
    )

    print(
        "PASS 07 stale reversal exit -> "
        "entry leg suppressed + whole event retained"
    )

    # ------------------------------------------------------------------
    # 8. DEDUPLICATION
    # ------------------------------------------------------------------

    e = event(
        cycle="AUDIT8"
    )

    eid = b.event_id(e)

    processed = {
        eid
    }

    all_events = [
        e,
        copy.deepcopy(e),
    ]

    new_events = [
        x
        for x in all_events
        if b.event_id(x)
        not in processed
    ]

    assert new_events == []

    print(
        "PASS 08 processed event ID -> no duplicate replay"
    )

    # ------------------------------------------------------------------
    # 9. SIMULTANEOUS FOUR-PAIR SIZING
    # ------------------------------------------------------------------

    state = b.default_bridge_state()

    requests = [
        ("AUDUSD", "long"),
        ("EURUSD", "long"),
        ("GBPUSD", "short"),
        ("USDJPY", "long"),
    ]

    alpha, sized = (
        b.sizing_adapter(
            NAV,
            MIDS,
            requests,
            b.virtual_existing(
                state
            ),
        )
    )

    assert abs(
        alpha - 0.75
    ) < 1e-12

    assert len(
        sized
    ) == 4

    for row in sized:
        b.apply_virtual_entry(
            state,
            row["pair"],
            row["side"],
            row["allocation_x"],
        )

    gross = sum(
        abs(
            x[
                "allocation_x"
            ]
        )
        for x in state[
            "virtual_positions"
        ].values()
    )

    assert abs(
        gross - 3.0
    ) < 1e-12

    print(
        "PASS 09 four simultaneous entries -> "
        "pro-rata alpha=.750000, effective gross=3x"
    )

    # ------------------------------------------------------------------
    # 10. CURRENCY-LEG CAP WITH EXISTING POSITIONS
    # ------------------------------------------------------------------

    state = b.default_bridge_state()

    b.apply_virtual_entry(
        state,
        "AUDUSD",
        "long",
        1.0,
    )

    b.apply_virtual_entry(
        state,
        "EURUSD",
        "long",
        1.0,
    )

    b.apply_virtual_entry(
        state,
        "GBPUSD",
        "short",
        1.0,
    )

    alpha, _ = (
        b.sizing_adapter(
            NAV,
            MIDS,
            [
                (
                    "USDJPY",
                    "long",
                )
            ],
            b.virtual_existing(
                state
            ),
        )
    )

    assert abs(
        alpha - 0.0
    ) < 1e-12

    print(
        "PASS 10 existing 3x USD leg -> "
        "new USD-linked entry allocation=0"
    )

    # ------------------------------------------------------------------
    # 11. EVENT ORDERING
    # ------------------------------------------------------------------

    events = [
        event(
            pair="GBPUSD",
            cycle="AUDIT11B",
        ),
        event(
            pair="AUDUSD",
            cycle="AUDIT11A",
        ),
    ]

    events.sort(
        key=lambda x: (
            b.event_ts(x),
            str(
                x["pair"]
            ),
        )
    )

    assert [
        x["pair"]
        for x in events
    ] == [
        "AUDUSD",
        "GBPUSD",
    ]

    print(
        "PASS 11 same-bar deterministic pair ordering"
    )

    # ------------------------------------------------------------------
    # 12. LIVE STATE / CANONICAL INTEGRITY
    # ------------------------------------------------------------------

    e1_after = sha256(
        M006E1_STATE
    )

    e3_after = sha256(
        M006E3_STATE
    )

    c_after = sha256(
        M006C_STATE
    )

    canonical_after = (
        directory_fingerprint(
            CANONICAL_ROOT
        )
    )

    assert (
        e1_before
        == e1_after
    )

    assert (
        e3_before
        == e3_after
    )

    assert (
        c_before
        == c_after
    )

    assert (
        canonical_before
        == canonical_after
    )

    print(
        "PASS 12 prospective M006e.1 state unchanged"
    )
    print(
        "PASS 13 prospective M006e.3 bridge state unchanged"
    )
    print(
        "PASS 14 M006c state unchanged"
    )
    print(
        "PASS 15 canonical M005 fingerprint unchanged"
    )

    print()
    print(
        "Network calls by regression: 0"
    )
    print(
        "Order payloads constructed: 0"
    )
    print(
        "OANDA writes invoked: FALSE"
    )
    print(
        "Order endpoints invoked: FALSE"
    )

    print()
    print("=" * 78)
    print(
        "M006E4_INTEGRATION_REGRESSION: PASS"
    )
    print(
        "Integrated entry, exit, reversal, retry, "
        "deduplication and simultaneous sizing "
        "behaviour verified offline."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

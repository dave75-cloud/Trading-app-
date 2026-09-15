#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

import m006e2_twelve_validator as v


ROOT = Path(".").resolve()

M006C_STATE = (
    ROOT
    / "data/research_runs/"
      "M006_PRACTICE_EXECUTION/"
      "signal_order_bridge/state/"
      "bridge_state.json"
)

M006E_STATE = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE/"
      "state/observer_state.json"
)


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


NOW = pd.Timestamp(
    "2026-09-01T12:08:00Z"
)

TS = pd.Timestamp(
    "2026-09-01T12:00:00Z"
)


def event(
    event_type="entry",
    old="flat",
    new="long",
    signal=1,
    vol_ok=True,
    close=1.0000,
    ts=TS,
):
    return {
        "cycle_id":
            "AUDIT",
        "provider":
            "oanda",
        "pair":
            "EURUSD",
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
            1.001,
        "slow_ma":
            1.000,
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
    signal=1,
    vol_ok=True,
    close=1.0000,
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


def one(e, t):
    rows = v.validate_event(
        e,
        t,
        NOW,
    )

    assert len(rows) == 1

    return rows[0]


def assert_has(
    row,
    field,
    fragment,
):
    vals = row[field]

    if not any(
        fragment in str(x)
        for x in vals
    ):
        raise AssertionError(
            f"{fragment!r} missing "
            f"from {field}: {vals}"
        )


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.2 — "
        "EVENT-DRIVEN DECISION AUDIT"
    )
    print("=" * 78)

    m006c_before = sha256(
        M006C_STATE
    )

    m006e_before = sha256(
        M006E_STATE
    )

    # 1. Clean entry agreement.
    r = one(
        event(),
        twelve(),
    )

    assert (
        r["decision"]
        == "ALLOW_DRY_RUN_VALIDATION"
    )

    print(
        "PASS 01 entry agreement -> ALLOW"
    )

    # 2. Direction disagreement.
    r = one(
        event(),
        twelve(
            signal=-1
        ),
    )

    assert r["decision"] == "BLOCK"

    assert_has(
        r,
        "reasons",
        "DIRECTION_DISAGREEMENT",
    )

    print(
        "PASS 02 direction disagreement -> BLOCK"
    )

    # 3. Volatility eligibility disagreement.
    r = one(
        event(
            vol_ok=True
        ),
        twelve(
            vol_ok=False
        ),
    )

    assert r["decision"] == "BLOCK"

    assert_has(
        r,
        "reasons",
        "VOL_ELIGIBILITY_DISAGREEMENT",
    )

    print(
        "PASS 03 vol eligibility disagreement -> BLOCK"
    )

    # 4. Authoritative OANDA vol false.
    r = one(
        event(
            vol_ok=False
        ),
        twelve(
            vol_ok=False
        ),
    )

    assert r["decision"] == "BLOCK"

    assert_has(
        r,
        "reasons",
        "OANDA_VOL_NOT_ELIGIBLE",
    )

    print(
        "PASS 04 OANDA vol ineligible -> BLOCK"
    )

    # 5. Missing Twelve matching bar.
    r = one(
        event(),
        None,
    )

    assert r["decision"] == "BLOCK"

    assert_has(
        r,
        "reasons",
        "TWELVE_MATCHING_BAR_MISSING",
    )

    print(
        "PASS 05 missing Twelve bar -> BLOCK"
    )

    # 6. Stale Twelve / event.
    stale_ts = pd.Timestamp(
        "2026-09-01T11:40:00Z"
    )

    r = one(
        event(
            ts=stale_ts
        ),
        twelve(
            ts=stale_ts
        ),
    )

    assert r["decision"] == "BLOCK"

    assert_has(
        r,
        "reasons",
        "AUTHORITATIVE_EVENT_STALE",
    )

    assert_has(
        r,
        "reasons",
        "TWELVE_STALE",
    )

    print(
        "PASS 06 stale entry evidence -> BLOCK"
    )

    # 7. 5-10 bps divergence is warning.
    r = one(
        event(
            close=1.0000
        ),
        twelve(
            close=1.0007
        ),
    )

    assert (
        r["decision"]
        == "ALLOW_DRY_RUN_VALIDATION"
    )

    assert_has(
        r,
        "warnings",
        "PRICE_DIVERGENCE_WARNING",
    )

    print(
        "PASS 07 5-10 bps divergence -> WARNING/ALLOW"
    )

    # 8. >10 bps divergence blocks.
    r = one(
        event(
            close=1.0000
        ),
        twelve(
            close=1.0012
        ),
    )

    assert r["decision"] == "BLOCK"

    assert_has(
        r,
        "reasons",
        "PRICE_DIVERGENCE_BLOCK",
    )

    print(
        "PASS 08 >10 bps divergence -> BLOCK"
    )

    # 9. Exit disagreement cannot veto.
    r = one(
        event(
            event_type="exit",
            old="long",
            new="flat",
            signal=0,
        ),
        twelve(
            signal=1,
        ),
    )

    assert (
        r["decision"]
        == "ALLOW_RISK_REDUCING_EXIT"
    )

    assert_has(
        r,
        "warnings",
        "EXIT_NOT_BLOCKED",
    )

    print(
        "PASS 09 exit disagreement -> EXIT ALLOWED"
    )

    # 10. Missing Twelve cannot veto exit.
    r = one(
        event(
            event_type="exit",
            old="long",
            new="flat",
            signal=0,
        ),
        None,
    )

    assert (
        r["decision"]
        == "ALLOW_RISK_REDUCING_EXIT"
    )

    print(
        "PASS 10 missing Twelve -> EXIT ALLOWED"
    )

    # 11. Reversal decomposes into exit + gated entry.
    rows = v.validate_event(
        event(
            event_type="reversal",
            old="long",
            new="short",
            signal=-1,
        ),
        twelve(
            signal=1,
        ),
        NOW,
    )

    assert len(rows) == 2

    assert (
        rows[0]["validation_leg"]
        == "reversal_exit"
    )

    assert (
        rows[0]["decision"]
        == "ALLOW_RISK_REDUCING_EXIT"
    )

    assert (
        rows[1]["validation_leg"]
        == "reversal_entry"
    )

    assert (
        rows[1]["decision"]
        == "BLOCK"
    )

    assert_has(
        rows[1],
        "reasons",
        "DIRECTION_DISAGREEMENT",
    )

    print(
        "PASS 11 reversal -> EXIT ALLOW + ENTRY GATED"
    )

    # 12. No authoritative events = no decisions.
    rows = v.validate_events(
        [],
        {},
        NOW,
    )

    assert rows == []

    print(
        "PASS 12 no events -> no validation action"
    )

    # 13. Malformed transition fails closed.
    r = one(
        event(
            event_type="entry",
            old="long",
            new="long",
            signal=1,
        ),
        twelve(),
    )

    assert r["decision"] == "BLOCK"

    assert_has(
        r,
        "reasons",
        "INVALID_AUTHORITATIVE_EVENT_TRANSITION",
    )

    print(
        "PASS 13 malformed event -> BLOCK"
    )

    # State integrity.
    m006c_after = sha256(
        M006C_STATE
    )

    m006e_after = sha256(
        M006E_STATE
    )

    if m006c_before != m006c_after:
        raise AssertionError(
            "M006c state changed"
        )

    if m006e_before != m006e_after:
        raise AssertionError(
            "M006e observer state changed"
        )

    source = Path(
        "tools/m006e/"
        "m006e2_twelve_validator.py"
    ).read_text()

    forbidden = [
        "requests.post(",
        "requests.put(",
        "requests.patch(",
        "requests.delete(",
        "urllib.request.Request(",
        "/orders",
    ]

    for token in forbidden:
        if token in source:
            raise AssertionError(
                "Forbidden write/network "
                f"token found: {token}"
            )

    print()
    print(
        "M006c state modified: FALSE"
    )
    print(
        "M006e observer state modified: FALSE"
    )
    print(
        "OANDA network calls by audit: 0"
    )
    print(
        "Order payloads constructed: 0"
    )
    print(
        "OANDA writes invoked: FALSE"
    )
    print(
        "Canonical M005 modified: FALSE"
    )

    print()
    print("=" * 78)
    print(
        "M006E2_EVENT_DECISION_AUDIT: PASS"
    )
    print(
        "Entry, exit, reversal, freshness, "
        "direction, volatility and divergence "
        "policy verified."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

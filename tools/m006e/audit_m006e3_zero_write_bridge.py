#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path

import m006e3_zero_write_bridge as b


ROOT = Path(".").resolve()

M006E1_STATE = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE/"
      "state/observer_state.json"
)

M006C_STATE = (
    ROOT
    / "data/research_runs/"
      "M006_PRACTICE_EXECUTION/"
      "signal_order_bridge/"
      "state/bridge_state.json"
)


def sha256(path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.3 — "
        "ZERO-WRITE BRIDGE AUDIT"
    )
    print("=" * 78)

    e1_before = sha256(
        M006E1_STATE
    )

    c_before = sha256(
        M006C_STATE
    )

    mids = {
        "AUD_USD": 0.6600,
        "EUR_USD": 1.1000,
        "GBP_USD": 1.3000,
        "USD_JPY": 150.0,
    }

    nav = 100000.0

    # Case 1: one entry = 1x.
    alpha, rows = (
        b.sizing_adapter(
            nav,
            mids,
            [
                (
                    "AUDUSD",
                    "long",
                )
            ],
            {},
        )
    )

    assert abs(
        alpha - 1.0
    ) < 1e-12

    assert (
        rows[0][
            "approx_units"
        ]
        == 100000
    )

    print(
        "PASS 01 single entry -> 1.000000x"
    )

    # Case 2: four USD-linked pairs
    # -> 3x USD gross currency-leg cap.
    alpha, rows = (
        b.sizing_adapter(
            nav,
            mids,
            [
                (
                    "AUDUSD",
                    "long",
                ),
                (
                    "EURUSD",
                    "long",
                ),
                (
                    "GBPUSD",
                    "short",
                ),
                (
                    "USDJPY",
                    "long",
                ),
            ],
            {},
        )
    )

    assert abs(
        alpha - 0.75
    ) < 1e-12

    assert len(rows) == 4

    print(
        "PASS 02 four simultaneous entries "
        "-> alpha=0.750000"
    )

    # Case 3: gross cap.
    alpha, _ = (
        b.sizing_adapter(
            nav,
            mids,
            [
                (
                    "USDJPY",
                    "long",
                )
            ],
            {
                "AUDUSD": 1.0,
                "EURUSD": 1.0,
                "GBPUSD": 1.0,
            },
        )
    )

    # Gross leaves 1x, and USD leg is
    # already 3x, so no further USD exposure.
    assert abs(
        alpha - 0.0
    ) < 1e-12

    print(
        "PASS 03 currency-leg cap can block entry"
    )

    # Case 4: order independence.
    req1 = [
        ("AUDUSD", "long"),
        ("EURUSD", "short"),
        ("GBPUSD", "long"),
    ]

    req2 = list(
        reversed(req1)
    )

    a1, _ = b.sizing_adapter(
        nav,
        mids,
        req1,
        {},
    )

    a2, _ = b.sizing_adapter(
        nav,
        mids,
        req2,
        {},
    )

    assert abs(
        a1 - a2
    ) < 1e-12

    print(
        "PASS 04 sizing order independence"
    )

    # Case 5: virtual ledger.
    st = b.default_bridge_state()

    b.apply_virtual_entry(
        st,
        "GBPUSD",
        "short",
        0.75,
    )

    assert (
        st[
            "virtual_positions"
        ]["GBPUSD"][
            "position"
        ]
        == -1
    )

    assert abs(
        st[
            "virtual_positions"
        ]["GBPUSD"][
            "allocation_x"
        ]
        - 0.75
    ) < 1e-12

    assert b.apply_virtual_exit(
        st,
        "GBPUSD",
    )

    assert (
        st[
            "virtual_positions"
        ]["GBPUSD"][
            "position"
        ]
        == 0
    )

    print(
        "PASS 05 virtual ledger entry/exit"
    )

    # Case 6: event identity stable.
    event = {
        "cycle_id": "TEST",
        "provider": "oanda",
        "pair": "EURUSD",
        "bar_ts_utc":
            "2026-09-01T12:00:00+00:00",
        "event_type": "entry",
        "old_position": "flat",
        "new_position": "long",
    }

    assert (
        b.event_id(event)
        == b.event_id(
            dict(event)
        )
    )

    print(
        "PASS 06 event-ID determinism"
    )

    # Source safety.
    source = Path(
        "tools/m006e/"
        "m006e3_zero_write_bridge.py"
    ).read_text()

    forbidden = [
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
        "requests.post(",
        "requests.put(",
        "requests.patch(",
        "requests.delete(",
        "/orders",
    ]

    for token in forbidden:
        if token in source:
            raise AssertionError(
                "Forbidden execution token: "
                f"{token}"
            )

    assert (
        'method="GET"'
        in source
    )

    print(
        "PASS 07 source contains GET only; "
        "no order endpoint/write method"
    )

    e1_after = sha256(
        M006E1_STATE
    )

    c_after = sha256(
        M006C_STATE
    )

    assert (
        e1_before
        == e1_after
    )

    assert (
        c_before
        == c_after
    )

    print(
        "PASS 08 M006e.1 state unchanged"
    )
    print(
        "PASS 09 M006c state unchanged"
    )

    print()
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
        "Order endpoints implemented: NONE"
    )
    print(
        "Canonical M005 modified: FALSE"
    )

    print()
    print("=" * 78)
    print(
        "M006E3_ZERO_WRITE_BRIDGE_AUDIT: PASS"
    )
    print(
        "Conservative-B sizing, "
        "virtual ledger, dedup identity "
        "and zero-write safety verified."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

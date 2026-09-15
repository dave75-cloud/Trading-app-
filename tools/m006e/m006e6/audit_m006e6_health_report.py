#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path

import m006e6_health_report as h


ROOT = Path(".").resolve()

E1_STATE = (
    ROOT
    / "data/research_runs/"
      "M006E_OANDA_AUTHORITATIVE/"
      "state/observer_state.json"
)

E3_STATE = (
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


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.6 — "
        "HEALTH REPORT AUDIT"
    )
    print("=" * 78)

    e1_before = sha256(
        E1_STATE
    )

    e3_before = sha256(
        E3_STATE
    )

    c_before = sha256(
        M006C_STATE
    )

    source = Path(
        "tools/m006e/m006e6/"
        "m006e6_health_report.py"
    ).read_text()

    forbidden = [
        "urllib.request",
        "requests.",
        "http://",
        "https://",
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
        "/orders",
        "launchctl load",
        "launchctl unload",
    ]

    for token in forbidden:
        if token in source:
            raise AssertionError(
                "Forbidden network/write token: "
                f"{token}"
            )

    print(
        "PASS 01 no network/order/scheduler-write capability"
    )

    required = [
        "orchestration_summary",
        "event_summary",
        "validation_summary",
        "bridge_report_summary",
        "observer_state_summary",
        "bridge_state_summary",
        "hash_summary",
        "health_flags",
    ]

    for token in required:
        if token not in source:
            raise AssertionError(
                "Missing reporting component: "
                f"{token}"
            )

    print(
        "PASS 02 required reporting components present"
    )

    hashes = h.hash_summary()

    assert hashes[
        "m006e1_observer"
    ]["match"]

    assert hashes[
        "m006e2_validator"
    ]["match"]

    assert hashes[
        "m006e3_bridge"
    ]["match"]

    assert hashes[
        "m006e4_regression"
    ]["match"]

    assert hashes[
        "m006e5_wrapper"
    ]["match"]

    print(
        "PASS 03 accepted core hashes match"
    )

    obs = (
        h.observer_state_summary()
    )

    bridge = (
        h.bridge_state_summary()
    )

    assert obs[
        "present"
    ]

    assert bridge[
        "present"
    ]

    print(
        "PASS 04 prospective observer/bridge states readable"
    )

    assert (
        bridge[
            "order_payloads_constructed"
        ]
        == 0
    )

    assert (
        bridge[
            "oanda_write_requests_performed"
        ]
        == 0
    )

    assert (
        bridge[
            "order_endpoints_invoked"
        ]
        is False
    )

    print(
        "PASS 05 zero-write bridge invariants clean"
    )

    e1_after = sha256(
        E1_STATE
    )

    e3_after = sha256(
        E3_STATE
    )

    c_after = sha256(
        M006C_STATE
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

    print(
        "PASS 06 M006e.1 state unchanged"
    )
    print(
        "PASS 07 M006e.3 state unchanged"
    )
    print(
        "PASS 08 M006c state unchanged"
    )

    print()
    print(
        "Network calls by audit: 0"
    )
    print(
        "External writes by audit: 0"
    )
    print(
        "Order capability: NONE"
    )

    print()
    print("=" * 78)
    print(
        "M006E6_HEALTH_REPORT_AUDIT: PASS"
    )
    print(
        "Read-only post-session reporting "
        "and frozen-core integrity verified."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

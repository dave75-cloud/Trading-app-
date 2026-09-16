#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path

import m006e8_reconciliation_timeline as r


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


def sha(path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.8 — "
        "RECONCILIATION AUDIT"
    )
    print("=" * 78)

    e1_before = sha(
        E1_STATE
    )

    e3_before = sha(
        E3_STATE
    )

    source = Path(
        "tools/m006e/m006e8/"
        "m006e8_reconciliation_timeline.py"
    ).read_text()

    forbidden = [
        "urllib.",
        "requests.",
        "http://",
        "https://",
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
        "/orders",
        "launchctl",
    ]

    for token in forbidden:
        if token in source:
            raise AssertionError(
                "Forbidden network/write token: "
                f"{token}"
            )

    print(
        "PASS 01 no network/order/scheduler capability"
    )

    e = {
        "cycle_id":
            "AUDIT",
        "provider":
            "oanda",
        "pair":
            "EURUSD",
        "bar_ts_utc":
            "2026-09-01T12:00:00+00:00",
        "event_type":
            "entry",
        "old_position":
            "flat",
        "new_position":
            "long",
        "close":
            1.1,
        "volatility":
            0.0006,
        "volatility_ok":
            True,
        "desired_delayed_signal":
            1,
    }

    e[
        "_event_id"
    ] = r.event_identity(
        e
    )

    validations = [
        {
            "pair":
                "EURUSD",
            "bar_ts_utc":
                "2026-09-01T12:00:00+00:00",
            "decision":
                "ALLOW_DRY_RUN_VALIDATION",
            "reasons":
                [],
        }
    ]

    actions = [
        {
            "event_id":
                e[
                    "_event_id"
                ],
            "leg":
                "entry",
            "decision":
                "ALLOW_DRY_RUN_PROPOSAL",
            "status":
                "SUPPRESSED_DRY_RUN",
            "allocation_x":
                1.0,
            "approx_units":
                60000,
        }
    ]

    provider = [
        {
            "pair":
                "EURUSD",
            "bar_ts_utc":
                "2026-09-01T12:00:00+00:00",
            "diagnostic_status":
                "AGREEMENT",
            "close_divergence_bps":
                0.1,
            "twelve_volatility":
                0.00061,
            "twelve_volatility_ok":
                True,
            "twelve_delayed_signal":
                1,
        }
    ]

    timeline = (
        r.build_timeline(
            [e],
            validations,
            actions,
            [],
            set(),
            provider,
        )
    )

    assert len(
        timeline
    ) == 1

    row = timeline[0]

    assert (
        row[
            "validation_decisions"
        ]
        == [
            "ALLOW_DRY_RUN_VALIDATION"
        ]
    )

    assert (
        row[
            "provider_path_status"
        ]
        == "AGREEMENT"
    )

    assert len(
        row[
            "bridge_actions"
        ]
    ) == 1

    assert (
        row[
            "retry_pending"
        ]
        is False
    )

    print(
        "PASS 02 event -> validation -> provider -> bridge linkage"
    )

    s = r.summary(
        timeline
    )

    assert (
        s[
            "events"
        ]
        == 1
    )

    assert (
        s[
            "with_validation"
        ]
        == 1
    )

    assert (
        s[
            "with_provider_path"
        ]
        == 1
    )

    assert (
        s[
            "with_bridge_action"
        ]
        == 1
    )

    print(
        "PASS 03 summary counts linked event correctly"
    )

    retry = {
        e[
            "_event_id"
        ]
    }

    timeline = (
        r.build_timeline(
            [e],
            validations,
            [],
            [],
            retry,
            provider,
        )
    )

    assert (
        timeline[0][
            "retry_pending"
        ]
        is True
    )

    print(
        "PASS 04 retry-pending linkage verified"
    )

    e1_after = sha(
        E1_STATE
    )

    e3_after = sha(
        E3_STATE
    )

    assert (
        e1_before
        == e1_after
    )

    assert (
        e3_before
        == e3_after
    )

    print(
        "PASS 05 M006e.1 state unchanged"
    )

    print(
        "PASS 06 M006e.3 state unchanged"
    )

    print()
    print(
        "Network calls by audit: 0"
    )
    print(
        "Order capability: NONE"
    )

    print()
    print("=" * 78)
    print(
        "M006E8_RECONCILIATION_AUDIT: PASS"
    )
    print(
        "Authoritative event, validator, provider-path "
        "and bridge decision linkage verified."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

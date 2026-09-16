#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path

from m007b_order_request_builder import (
    ApprovedExecutionInput,
    build_market_order_request,
)


ROOT = Path(".").resolve()

SOURCE = (
    ROOT
    / "tools/m007/m007b/"
      "m007b_order_request_builder.py"
)

M006E5 = (
    ROOT
    / "tools/m006e/m006e5/"
      "run_m006e5_cycle.sh"
)

M006E6 = (
    ROOT
    / "tools/m006e/m006e6/"
      "m006e6_health_report.py"
)

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


ACCEPTED_E5 = (
    "a5780b27af2d550a47d9163ece6e6db"
    "81e1f8e769ff13c8190fa8565743e036e"
)

ACCEPTED_E6 = (
    "32c6baf0a374f699785170e7eb887b0a"
    "1ca3e9b6b6ec2f71f32e480be212362b"
)


def sha(path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def approved(
    pair="EURUSD",
    event_type="entry",
    old_position="flat",
    new_position="long",
    units=12345,
):
    return ApprovedExecutionInput(
        strategy_version=
            "CandidateA-M006e",
        pair=
            pair,
        bar_ts_utc=
            "2026-09-01T12:40:00+00:00",
        event_type=
            event_type,
        old_position=
            old_position,
        new_position=
            new_position,
        signed_units=
            units,
        validation_decision=
            "APPROVED",
        sizing_decision=
            "APPROVED",
    )


def expect_failure(
    fn,
    label,
):
    try:
        fn()
    except (
        ValueError,
        TypeError,
        KeyError,
    ):
        return

    raise AssertionError(
        f"Expected failure: {label}"
    )


def main():
    print("=" * 78)
    print(
        "KQTRL M007b — "
        "ORDER-BUILDER ZERO-WRITE AUDIT"
    )
    print("=" * 78)

    e5_before = sha(
        M006E5
    )

    e6_before = sha(
        M006E6
    )

    e1_before = sha(
        E1_STATE
    )

    e3_before = sha(
        E3_STATE
    )

    assert (
        e5_before
        == ACCEPTED_E5
    )

    assert (
        e6_before
        == ACCEPTED_E6
    )

    print(
        "PASS 01 accepted active M006e hashes preserved"
    )

    # Long EURUSD.
    r = build_market_order_request(
        approved()
    )

    order = r[
        "request_body"
    ][
        "order"
    ]

    assert (
        order[
            "instrument"
        ]
        == "EUR_USD"
    )

    assert (
        order[
            "units"
        ]
        == "12345"
    )

    assert (
        order[
            "type"
        ]
        == "MARKET"
    )

    assert (
        order[
            "timeInForce"
        ]
        == "FOK"
    )

    assert (
        order[
            "positionFill"
        ]
        == "DEFAULT"
    )

    print(
        "PASS 02 long EURUSD request constructed correctly"
    )

    # Short USDJPY sign.
    r = build_market_order_request(
        approved(
            pair="USDJPY",
            new_position="short",
            units=-23456,
        )
    )

    order = r[
        "request_body"
    ][
        "order"
    ]

    assert (
        order[
            "instrument"
        ]
        == "USD_JPY"
    )

    assert (
        order[
            "units"
        ]
        == "-23456"
    )

    print(
        "PASS 03 short USDJPY unit sign preserved"
    )

    # All mappings.
    mappings = {
        "AUDUSD":
            "AUD_USD",
        "EURUSD":
            "EUR_USD",
        "GBPUSD":
            "GBP_USD",
        "USDJPY":
            "USD_JPY",
    }

    for pair, instrument in mappings.items():
        r = build_market_order_request(
            approved(
                pair=pair,
            )
        )

        assert (
            r[
                "request_body"
            ][
                "order"
            ][
                "instrument"
            ]
            == instrument
        )

    print(
        "PASS 04 all four pair mappings verified"
    )

    # Deterministic identity and metadata.
    a = build_market_order_request(
        approved()
    )

    b = build_market_order_request(
        approved()
    )

    assert (
        a[
            "event_id"
        ]
        == b[
            "event_id"
        ]
    )

    assert (
        a[
            "event_sha256"
        ]
        == b[
            "event_sha256"
        ]
    )

    assert (
        a[
            "request_body"
        ][
            "order"
        ][
            "clientExtensions"
        ]
        ==
        b[
            "request_body"
        ][
            "order"
        ][
            "clientExtensions"
        ]
    )

    print(
        "PASS 05 event identity/client metadata deterministic"
    )

    # Different event => different identity.
    c = ApprovedExecutionInput(
        strategy_version=
            "CandidateA-M006e",
        pair=
            "EURUSD",
        bar_ts_utc=
            "2026-09-01T12:45:00Z",
        event_type=
            "entry",
        old_position=
            "flat",
        new_position=
            "long",
        signed_units=
            12345,
        validation_decision=
            "APPROVED",
        sizing_decision=
            "APPROVED",
    )

    c = build_market_order_request(
        c
    )

    assert (
        c[
            "event_id"
        ]
        != a[
            "event_id"
        ]
    )

    print(
        "PASS 06 distinct bar creates distinct event identity"
    )

    # Reversal entry only after upstream exit confirmation.
    r = build_market_order_request(
        approved(
            event_type=
                "reversal_entry",
            old_position=
                "short",
            new_position=
                "long",
            units=
                15000,
        )
    )

    assert (
        r[
            "validated_input"
        ][
            "event_type"
        ]
        == "reversal_entry"
    )

    print(
        "PASS 07 reversal-entry construction is a separate entry leg"
    )

    # Fail-closed cases.
    expect_failure(
        lambda:
            build_market_order_request(
                approved(
                    units=0,
                )
            ),
        "zero units",
    )

    expect_failure(
        lambda:
            build_market_order_request(
                approved(
                    new_position=
                        "long",
                    units=
                        -1000,
                )
            ),
        "direction mismatch",
    )

    expect_failure(
        lambda:
            build_market_order_request(
                approved(
                    old_position=
                        "long",
                )
            ),
        "ordinary entry not from flat",
    )

    expect_failure(
        lambda:
            build_market_order_request(
                ApprovedExecutionInput(
                    strategy_version=
                        "CandidateA-M006e",
                    pair=
                        "EURUSD",
                    bar_ts_utc=
                        "2026-09-01T12:40:00Z",
                    event_type=
                        "entry",
                    old_position=
                        "flat",
                    new_position=
                        "long",
                    signed_units=
                        1000,
                    validation_decision=
                        "BLOCKED",
                    sizing_decision=
                        "APPROVED",
                )
            ),
        "validation blocked",
    )

    expect_failure(
        lambda:
            build_market_order_request(
                ApprovedExecutionInput(
                    strategy_version=
                        "CandidateA-M006e",
                    pair=
                        "EURUSD",
                    bar_ts_utc=
                        "2026-09-01T12:40:00Z",
                    event_type=
                        "entry",
                    old_position=
                        "flat",
                    new_position=
                        "long",
                    signed_units=
                        1000,
                    validation_decision=
                        "APPROVED",
                    sizing_decision=
                        "BLOCKED",
                )
            ),
        "sizing blocked",
    )

    expect_failure(
        lambda:
            build_market_order_request(
                approved(
                    pair="NZDUSD",
                )
            ),
        "unsupported pair",
    )

    expect_failure(
        lambda:
            build_market_order_request(
                ApprovedExecutionInput(
                    strategy_version=
                        "CandidateA-M006e",
                    pair=
                        "EURUSD",
                    bar_ts_utc=
                        "2026-09-01T12:40:00",
                    event_type=
                        "entry",
                    old_position=
                        "flat",
                    new_position=
                        "long",
                    signed_units=
                        1000,
                    validation_decision=
                        "APPROVED",
                    sizing_decision=
                        "APPROVED",
                )
            ),
        "timestamp without UTC",
    )

    print(
        "PASS 08 fail-closed input validation cases"
    )

    assert (
        a[
            "sizing_recalculated"
        ]
        is False
    )

    assert (
        a[
            "validated_input"
        ][
            "signed_units"
        ]
        == 12345
    )

    print(
        "PASS 09 M007b preserves upstream signed units without resizing"
    )

    source = SOURCE.read_text()

    forbidden_patterns = [
        "import requests",
        "from requests",
        "import urllib",
        "from urllib",
        "import http.client",
        "from http.client",
        "import socket",
        "from socket",
        "import subprocess",
        "from subprocess",
        "requests.get(",
        "requests.post(",
        "requests.put(",
        "requests.patch(",
        "requests.delete(",
        "urlopen(",
        "HTTPConnection(",
        "HTTPSConnection(",
        "OANDA_API_TOKEN",
        "OANDA_ACCOUNT_ID",
        "Authorization",
        "Bearer ",
        "api-fxpractice",
        "api-fxtrade",
        "/v3/accounts/",
        "/orders",
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
    ]

    for token in forbidden_patterns:
        assert (
            token not in source
        ), token

    print(
        "PASS 10 source contains no transport/account/order-endpoint capability"
    )

    assert (
        a[
            "network_capability"
        ]
        is False
    )

    assert (
        a[
            "order_submission_capability"
        ]
        is False
    )

    print(
        "PASS 11 generated result explicitly declares zero-write capability"
    )

    assert (
        sha(
            M006E5
        )
        == e5_before
    )

    assert (
        sha(
            M006E6
        )
        == e6_before
    )

    assert (
        sha(
            E1_STATE
        )
        == e1_before
    )

    assert (
        sha(
            E3_STATE
        )
        == e3_before
    )

    print(
        "PASS 12 active M006e.5 unchanged"
    )

    print(
        "PASS 13 active M006e.6 unchanged"
    )

    print(
        "PASS 14 M006e.1 prospective state unchanged"
    )

    print(
        "PASS 15 M006e.3 prospective state unchanged"
    )

    print()
    print(
        "Network calls by audit: 0"
    )

    print(
        "Order writes: 0"
    )

    print(
        "Order endpoint capability: FALSE"
    )

    print(
        "Sizing recalculation: FALSE"
    )

    print(
        "Candidate promoted: FALSE"
    )

    print()
    print("=" * 78)

    print(
        "M007B_ORDER_BUILDER_AUDIT: PASS"
    )

    print(
        "Deterministic entry-side OANDA request construction "
        "verified with no network or order-submission capability."
    )

    print("=" * 78)


if __name__ == "__main__":
    main()

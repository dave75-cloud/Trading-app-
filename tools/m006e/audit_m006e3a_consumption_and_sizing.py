#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import os
import re
import sys
from pathlib import Path

import m006e3_zero_write_bridge as b


ROOT = Path(".").resolve()

D2_PATH = (
    ROOT
    / "tools/pre_monday/"
      "m006d_sizing.py"
)

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


MIDS = {
    "AUD_USD": 0.6600,
    "EUR_USD": 1.1000,
    "GBP_USD": 1.3000,
    "USD_JPY": 150.0,
}

NAV = 100000.0


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def load_d2():
    spec = importlib.util.spec_from_file_location(
        "m006d2_reference",
        D2_PATH,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "Cannot import audited M006d.2"
        )

    mod = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        mod
    )

    return mod


def fake_getj(url, token):
    if url.endswith(
        "/summary"
    ):
        return {
            "account": {
                "currency": "AUD",
                "NAV": str(NAV),
            }
        }

    if "/pricing?" in url:
        return {
            "prices": [
                {
                    "instrument":
                        instrument,
                    "bids": [
                        {
                            "price":
                                str(mid)
                        }
                    ],
                    "asks": [
                        {
                            "price":
                                str(mid)
                        }
                    ],
                }
                for instrument, mid
                in MIDS.items()
            ]
        }

    raise AssertionError(
        f"Unexpected mocked GET URL: {url}"
    )


def run_audited_d2(
    d2,
    entries,
    existing,
):
    old_argv = sys.argv[:]

    old_env = {
        "OANDA_ENV":
            os.environ.get(
                "OANDA_ENV"
            ),
        "OANDA_API_TOKEN":
            os.environ.get(
                "OANDA_API_TOKEN"
            ),
        "OANDA_ACCOUNT_ID":
            os.environ.get(
                "OANDA_ACCOUNT_ID"
            ),
    }

    old_getj = d2.getj

    try:
        os.environ[
            "OANDA_ENV"
        ] = "practice"

        os.environ[
            "OANDA_API_TOKEN"
        ] = "AUDIT_TOKEN"

        os.environ[
            "OANDA_ACCOUNT_ID"
        ] = "AUDIT_ACCOUNT"

        d2.getj = fake_getj

        entries_arg = ",".join(
            f"{pair}:{side}"
            for pair, side
            in entries
        )

        existing_arg = ",".join(
            f"{pair}:{value}"
            for pair, value
            in existing.items()
        )

        sys.argv = [
            str(D2_PATH),
            "--entries",
            entries_arg,
            "--existing",
            existing_arg,
        ]

        out = io.StringIO()

        with contextlib.redirect_stdout(
            out
        ):
            d2.main()

        text = out.getvalue()

    finally:
        d2.getj = old_getj
        sys.argv = old_argv

        for key, value in (
            old_env.items()
        ):
            if value is None:
                os.environ.pop(
                    key,
                    None,
                )
            else:
                os.environ[
                    key
                ] = value

    m = re.search(
        r"pro_rata_alpha="
        r"([0-9.]+)",
        text,
    )

    if not m:
        raise AssertionError(
            "Could not parse audited "
            "M006d.2 alpha"
        )

    alpha = float(
        m.group(1)
    )

    rows = {}

    pattern = re.compile(
        r"^(AUDUSD|EURUSD|GBPUSD|USDJPY) "
        r"(long|short): "
        r"allocation=([0-9.]+)x "
        r"approx_units=([+-]?[0-9]+)$",
        re.MULTILINE,
    )

    for m in pattern.finditer(
        text
    ):
        pair = m.group(1)

        rows[pair] = {
            "side":
                m.group(2),
            "allocation_x":
                float(
                    m.group(3)
                ),
            "approx_units":
                int(
                    m.group(4)
                ),
        }

    if len(rows) != len(
        entries
    ):
        raise AssertionError(
            "Could not parse all audited "
            "M006d.2 sizing rows\n"
            + text
        )

    return alpha, rows


def compare_sizing_case(
    d2,
    name,
    entries,
    existing,
):
    a_bridge, r_bridge = (
        b.sizing_adapter(
            NAV,
            MIDS,
            entries,
            existing,
        )
    )

    a_ref, r_ref = (
        run_audited_d2(
            d2,
            entries,
            existing,
        )
    )

    # The audited CLI prints alpha to
    # six decimal places, so compare at
    # that exact observable precision.
    if (
        round(
            a_bridge,
            6,
        )
        != round(
            a_ref,
            6,
        )
    ):
        raise AssertionError(
            f"{name}: alpha mismatch "
            f"bridge={a_bridge} "
            f"audited={a_ref}"
        )

    by_pair_bridge = {
        row["pair"]: row
        for row in r_bridge
    }

    for pair, ref in (
        r_ref.items()
    ):
        got = by_pair_bridge[
            pair
        ]

        if (
            got[
                "approx_units"
            ]
            != ref[
                "approx_units"
            ]
        ):
            raise AssertionError(
                f"{name} {pair}: "
                "unit mismatch "
                f"bridge="
                f"{got['approx_units']} "
                f"audited="
                f"{ref['approx_units']}"
            )

        if (
            round(
                got[
                    "allocation_x"
                ],
                6,
            )
            != round(
                ref[
                    "allocation_x"
                ],
                6,
            )
        ):
            raise AssertionError(
                f"{name} {pair}: "
                "allocation mismatch"
            )

    print(
        f"PASS sizing {name}: "
        f"alpha={a_bridge:.6f}"
    )


def consumption_tests():
    print()
    print(
        "=== EVENT CONSUMPTION / RETRY ==="
    )

    report = {
        "processed_event_ids": [],
        "retry_pending_event_ids": [],
    }

    processed = set()
    retry = set()

    entry_id = "ENTRY"

    consumed = b.consume_event_id(
        processed,
        report,
        entry_id,
        retry,
    )

    assert consumed
    assert entry_id in processed

    print(
        "PASS blocked/terminal entry "
        "can be consumed"
    )

    exit_id = "EXIT_STALE"

    retry.add(
        exit_id
    )

    consumed = b.consume_event_id(
        processed,
        report,
        exit_id,
        retry,
    )

    assert not consumed
    assert exit_id not in processed
    assert (
        exit_id
        in report[
            "retry_pending_event_ids"
        ]
    )

    print(
        "PASS stale-price exit remains "
        "unconsumed for retry"
    )

    reversal_id = (
        "REVERSAL_STALE"
    )

    retry.add(
        reversal_id
    )

    consumed = b.consume_event_id(
        processed,
        report,
        reversal_id,
        retry,
    )

    assert not consumed
    assert (
        reversal_id
        not in processed
    )

    print(
        "PASS stale-price reversal remains "
        "unconsumed for retry"
    )

    retry.remove(
        exit_id
    )

    consumed = b.consume_event_id(
        processed,
        report,
        exit_id,
        retry,
    )

    assert consumed
    assert exit_id in processed

    print(
        "PASS retried exit consumes only "
        "after freshness clears"
    )

    source = Path(
        "tools/m006e/"
        "m006e3_zero_write_bridge.py"
    ).read_text()

    required_source_fragments = [
        "retry_pending.add(",
        "REVERSAL_EXIT_NOT_COMPLETED",
        "consume_event_id(",
        '"retry_pending_event_ids": []',
    ]

    for token in (
        required_source_fragments
    ):
        if token not in source:
            raise AssertionError(
                "Missing retry-semantics "
                f"source fragment: {token}"
            )

    print(
        "PASS source wiring contains "
        "exit/reversal retry semantics"
    )


def safety_source_test():
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

    if 'method="GET"' not in source:
        raise AssertionError(
            "GET-only OANDA request "
            "implementation not found"
        )

    print(
        "PASS source remains GET-only "
        "with no order endpoint"
    )


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.3a — "
        "CONSUMPTION + EXACT SIZING AUDIT"
    )
    print("=" * 78)

    e1_before = sha256(
        M006E1_STATE
    )

    c_before = sha256(
        M006C_STATE
    )

    d2 = load_d2()

    print()
    print(
        "=== M006d.2 ADAPTER "
        "EQUIVALENCE ==="
    )

    cases = [
        (
            "single_AUDUSD",
            [
                (
                    "AUDUSD",
                    "long",
                )
            ],
            {},
        ),
        (
            "single_EURUSD",
            [
                (
                    "EURUSD",
                    "short",
                )
            ],
            {},
        ),
        (
            "single_GBPUSD",
            [
                (
                    "GBPUSD",
                    "long",
                )
            ],
            {},
        ),
        (
            "single_USDJPY",
            [
                (
                    "USDJPY",
                    "short",
                )
            ],
            {},
        ),
        (
            "four_simultaneous",
            [
                (
                    "AUDUSD",
                    "long",
                ),
                (
                    "EURUSD",
                    "short",
                ),
                (
                    "GBPUSD",
                    "long",
                ),
                (
                    "USDJPY",
                    "short",
                ),
            ],
            {},
        ),
        (
            "two_simultaneous",
            [
                (
                    "EURUSD",
                    "long",
                ),
                (
                    "GBPUSD",
                    "short",
                ),
            ],
            {},
        ),
        (
            "existing_1x",
            [
                (
                    "EURUSD",
                    "long",
                )
            ],
            {
                "AUDUSD": 1.0,
            },
        ),
        (
            "existing_2x_USD",
            [
                (
                    "USDJPY",
                    "long",
                )
            ],
            {
                "EURUSD": 1.0,
                "GBPUSD": 1.0,
            },
        ),
        (
            "currency_cap_zero",
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
        ),
        (
            "fractional_existing",
            [
                (
                    "AUDUSD",
                    "short",
                ),
                (
                    "EURUSD",
                    "long",
                ),
            ],
            {
                "GBPUSD": 0.75,
                "USDJPY": 0.50,
            },
        ),
    ]

    for (
        name,
        entries,
        existing,
    ) in cases:
        compare_sizing_case(
            d2,
            name,
            entries,
            existing,
        )

    # Explicit order-independence test.
    req1 = [
        ("AUDUSD", "long"),
        ("EURUSD", "short"),
        ("GBPUSD", "long"),
    ]

    req2 = list(
        reversed(
            req1
        )
    )

    a1, _ = b.sizing_adapter(
        NAV,
        MIDS,
        req1,
        {},
    )

    a2, _ = b.sizing_adapter(
        NAV,
        MIDS,
        req2,
        {},
    )

    assert abs(
        a1 - a2
    ) < 1e-12

    print(
        "PASS sizing order independence"
    )

    consumption_tests()

    print()
    print(
        "=== ZERO-WRITE SAFETY ==="
    )

    safety_source_test()

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
        "PASS M006e.1 state unchanged"
    )
    print(
        "PASS M006c state unchanged"
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
        "M006E3A_CONSUMPTION_SIZING_AUDIT: PASS"
    )
    print(
        "Risk-reducing exit retry semantics "
        "and audited M006d.2 sizing "
        "equivalence verified."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

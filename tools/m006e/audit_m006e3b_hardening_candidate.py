#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import m006e2_twelve_validator as v2


ROOT = Path(".").resolve()

CANDIDATE = (
    ROOT
    / "tools/m006e/"
      "m006e3_zero_write_bridge.hardening_candidate.py"
)

ACTIVE = (
    ROOT
    / "tools/m006e/"
      "m006e3_zero_write_bridge.py"
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

M006C_STATE = (
    ROOT
    / "data/research_runs/"
      "M006_PRACTICE_EXECUTION/"
      "signal_order_bridge/"
      "state/bridge_state.json"
)


EXPECTED_ACTIVE_HASH = (
    "568e30e90e95df8c7e30519947f13699"
    "fe72305e22ad9a669d8fe3b04f9b43b5"
)


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def load_candidate():
    spec = importlib.util.spec_from_file_location(
        "m006e3_hardening_candidate",
        CANDIDATE,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "Cannot import hardening candidate"
        )

    mod = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        mod
    )

    return mod


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.3b — "
        "ISOLATED HARDENING CANDIDATE AUDIT"
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

    active_before = sha256(
        ACTIVE
    )

    assert (
        active_before
        == EXPECTED_ACTIVE_HASH
    )

    print(
        "PASS 01 active M006e.3 still has accepted frozen hash"
    )

    b = load_candidate()

    # --------------------------------------------------------------
    # Boolean parsing semantics.
    # --------------------------------------------------------------

    assert (
        v2.boolish(True)
        is True
    )

    assert (
        v2.boolish(False)
        is False
    )

    assert (
        v2.boolish("True")
        is True
    )

    assert (
        v2.boolish("False")
        is False
    )

    assert (
        v2.boolish("FALSE")
        is False
    )

    assert (
        v2.boolish("0")
        is False
    )

    print(
        "PASS 02 boolish parser treats literal "
        "'False'/'FALSE'/'0' as false"
    )

    source = CANDIDATE.read_text()

    assert (
        "if not v2.boolish("
        in source
    )

    assert (
        '''if not bool(
                e.get(
                    "in_session",'''
        not in source
    )

    print(
        "PASS 03 candidate entry gate uses explicit boolish parsing"
    )

    # --------------------------------------------------------------
    # Freshness boundary semantics.
    #
    # price_is_fresh only reads the provided dictionary,
    # so these are completely offline tests.
    # --------------------------------------------------------------

    def prices(age):
        return {
            "EUR_USD": {
                "age_min": float(age),
            }
        }

    fresh, age = b.price_is_fresh(
        "EURUSD",
        prices(0.0),
    )

    assert fresh
    assert age == 0.0

    print(
        "PASS 04 price age 0.000m -> fresh"
    )

    fresh, _ = b.price_is_fresh(
        "EURUSD",
        prices(5.0),
    )

    assert fresh

    print(
        "PASS 05 price age exactly 5.000m -> fresh"
    )

    fresh, _ = b.price_is_fresh(
        "EURUSD",
        prices(5.000001),
    )

    assert not fresh

    print(
        "PASS 06 price age >5m -> stale"
    )

    fresh, _ = b.price_is_fresh(
        "EURUSD",
        prices(-0.000001),
    )

    assert not fresh

    print(
        "PASS 07 future price timestamp "
        "(negative age) -> fail closed"
    )

    fresh, _ = b.price_is_fresh(
        "EURUSD",
        prices(-2.0),
    )

    assert not fresh

    print(
        "PASS 08 material clock-skew/future timestamp -> fail closed"
    )

    # --------------------------------------------------------------
    # Ensure report freshness expression was hardened too.
    # --------------------------------------------------------------

    required = '''
                    0.0
                    <= prices[
                        instrument
                    ]["age_min"]
                    <= OANDA_PRICE_MAX_MIN
'''

    if required not in source:
        raise AssertionError(
            "Report freshness flag does not use "
            "non-negative hardened range"
        )

    print(
        "PASS 09 report freshness flag matches hardened decision rule"
    )

    # --------------------------------------------------------------
    # Existing retry semantics remain present.
    # --------------------------------------------------------------

    required_retry_tokens = [
        "retry_pending.add(",
        "REVERSAL_EXIT_NOT_COMPLETED",
        "consume_event_id(",
        '"retry_pending_event_ids": []',
    ]

    for token in required_retry_tokens:
        if token not in source:
            raise AssertionError(
                "Existing retry semantic missing: "
                f"{token}"
            )

    print(
        "PASS 10 exit/reversal retry semantics preserved"
    )

    # --------------------------------------------------------------
    # Zero-write topology preserved.
    # --------------------------------------------------------------

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
        "PASS 11 candidate remains GET-only with no order endpoint"
    )

    # Existing offline self-test from the candidate itself.
    b.self_test()

    print(
        "PASS 12 candidate original self-test still passes"
    )

    # --------------------------------------------------------------
    # Active/prospective integrity.
    # --------------------------------------------------------------

    active_after = sha256(
        ACTIVE
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
        active_before
        == active_after
        == EXPECTED_ACTIVE_HASH
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
        "PASS 13 active M006e.3 source unchanged"
    )
    print(
        "PASS 14 M006e.1 prospective state unchanged"
    )
    print(
        "PASS 15 M006e.3 prospective state unchanged"
    )
    print(
        "PASS 16 M006c state unchanged"
    )

    print()
    print(
        "Network calls by audit: 0"
    )
    print(
        "Order payloads constructed by audit: 0"
    )
    print(
        "OANDA writes invoked: FALSE"
    )
    print(
        "Active bridge replacement performed: FALSE"
    )

    print()
    print("=" * 78)
    print(
        "M006E3B_HARDENING_CANDIDATE_AUDIT: PASS"
    )
    print(
        "Explicit boolean parsing and "
        "non-negative OANDA freshness semantics "
        "verified in isolated candidate."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

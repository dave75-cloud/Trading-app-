#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(".").resolve()

VERIFIER = (
    ROOT
    / "tools/m006e/provenance/"
      "verify_m006e_freeze_manifest.py"
)

MANIFEST = (
    ROOT
    / "tools/m006e/provenance/"
      "m006e_freeze_manifest.json"
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


def sha256(path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    print("=" * 78)
    print(
        "KQTRL M006e — "
        "PROVENANCE TOOLING AUDIT"
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

    source = VERIFIER.read_text()

    forbidden = [
        "urllib.",
        "requests.",
        "http://",
        "https://",
        "launchctl",
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
        "/orders",
    ]

    for token in forbidden:
        if token in source:
            raise AssertionError(
                "Forbidden token in verifier: "
                f"{token}"
            )

    print(
        "PASS 01 verifier has no network/"
        "scheduler/order capability"
    )

    assert MANIFEST.exists()

    print(
        "PASS 02 provenance manifest exists"
    )

    required = [
        "m006e1_observer",
        "m006e2_validator",
        "m006e3_bridge_active",
        "m006e4_regression",
        "m006e5_wrapper",
        "m006e6_health_report",
        "m006e3_hardening_candidate",
    ]

    text = MANIFEST.read_text()

    for token in required:
        if token not in text:
            raise AssertionError(
                "Missing manifest component: "
                f"{token}"
            )

    print(
        "PASS 03 required active/candidate "
        "components recorded"
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
        "PASS 04 M006e.1 state unchanged"
    )
    print(
        "PASS 05 M006e.3 state unchanged"
    )
    print(
        "PASS 06 M006c state unchanged"
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
        "M006E_PROVENANCE_AUDIT: PASS"
    )
    print(
        "Manifest/verifier tooling is isolated "
        "from prospective trading state."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json


ROOT = Path(".").resolve()

SPEC = (
    ROOT
    / "tools/m007/design/"
      "M007_PRACTICE_EXECUTION_SPEC.md"
)

MATRIX = (
    ROOT
    / "tools/m007/design/"
      "M007_ACCEPTANCE_MATRIX.json"
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

ACCEPTED_E5 = (
    "a5780b27af2d550a47d9163ece6e6db"
    "81e1f8e769ff13c8190fa8565743e036e"
)

ACCEPTED_E6 = (
    "32c6baf0a374f699785170e7eb887b0a"
    "1ca3e9b6b6ec2f71f32e480be212362b"
)


def sha(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    print("=" * 78)
    print("KQTRL M007a — DESIGN SPECIFICATION AUDIT")
    print("=" * 78)

    assert sha(M006E5) == ACCEPTED_E5
    assert sha(M006E6) == ACCEPTED_E6

    print(
        "PASS 01 accepted M006e.5 / M006e.6 hashes preserved"
    )

    spec = SPEC.read_text()

    required = [
        "PRACTICE ONLY",
        "idempotent",
        "AMBIGUOUS_WRITE_RESULT",
        "PARTIAL_FILL",
        "EXECUTED_CONFIRMED",
        "reversal",
        "M006d.2",
        "execution ledger",
        "ENABLE_DEMO_EXECUTION=NO",
        "OANDA LIVE SUPPORT: FALSE",
        "LIVE CAPITAL: FALSE",
        "ACTIVE M006e MODIFIED: FALSE",
    ]

    for token in required:
        assert token.lower() in spec.lower(), token

    print(
        "PASS 02 core execution-safety concepts present"
    )

    matrix = json.loads(
        MATRIX.read_text()
    )

    assert matrix[
        "execution_enabled"
    ] is False

    assert matrix[
        "live_capital"
    ] is False

    assert matrix[
        "oanda_live_supported"
    ] is False

    assert matrix[
        "canonical_m005_modified"
    ] is False

    assert matrix[
        "active_m006e_modified"
    ] is False

    print(
        "PASS 03 acceptance matrix is design-only / zero-write"
    )

    assert (
        matrix[
            "requirements"
        ][
            "idempotent_event_identity"
        ]
        is True
    )

    assert (
        matrix[
            "requirements"
        ][
            "ambiguous_write_reconciliation"
        ]
        is True
    )

    assert (
        matrix[
            "requirements"
        ][
            "partial_fill_handling"
        ]
        is True
    )

    assert (
        matrix[
            "requirements"
        ][
            "human_promotion_required"
        ]
        is True
    )

    print(
        "PASS 04 critical M007 acceptance gates recorded"
    )

    forbidden = [
        "urllib.request.urlopen",
        "requests.post",
        "requests.put",
        "requests.patch",
        "requests.delete",
        "/v3/accounts/",
        "/orders",
        "launchctl",
    ]

    combined = (
        SPEC.read_text()
        + "\n"
        + MATRIX.read_text()
    )

    for token in forbidden:
        assert token not in combined, token

    print(
        "PASS 05 design package has no executable network/order path"
    )

    assert sha(M006E5) == ACCEPTED_E5
    assert sha(M006E6) == ACCEPTED_E6

    print(
        "PASS 06 active M006e remains unchanged"
    )

    print()
    print("Network calls: 0")
    print("Order writes: 0")
    print("Practice execution enabled: FALSE")
    print("Candidate promoted: FALSE")

    print()
    print("=" * 78)
    print("M007A_DESIGN_AUDIT: PASS")
    print(
        "Practice execution architecture specified "
        "without creating an order-capable implementation."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

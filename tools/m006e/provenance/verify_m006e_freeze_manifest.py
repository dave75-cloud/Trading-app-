#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(".").resolve()

MANIFEST = (
    ROOT
    / "tools/m006e/provenance/"
      "m006e_freeze_manifest.json"
)


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def verify_group(
    name,
    group,
):
    print()
    print(f"=== {name} ===")

    failures = 0

    for key, row in group.items():
        path = ROOT / row["path"]

        expected = row["sha256"]

        actual = sha256(path)

        ok = (
            actual == expected
        )

        print(
            f"{key}: "
            f"{'PASS' if ok else 'FAIL'}"
        )

        print(
            "  path:",
            row["path"],
        )

        print(
            "  expected:",
            expected,
        )

        print(
            "  actual:  ",
            actual,
        )

        if not ok:
            failures += 1

    return failures


def main():
    print("=" * 78)
    print(
        "KQTRL M006e — "
        "FREEZE MANIFEST VERIFIER"
    )
    print("=" * 78)

    if not MANIFEST.exists():
        raise SystemExit(
            "FAIL_CLOSED: manifest missing"
        )

    manifest = json.loads(
        MANIFEST.read_text()
    )

    print(
        "Manifest version:",
        manifest.get(
            "manifest_version"
        ),
    )

    print(
        "Status:",
        manifest.get(
            "status"
        ),
    )

    print(
        "Execution mode:",
        manifest.get(
            "execution_mode"
        ),
    )

    failures = 0

    failures += verify_group(
        "ACTIVE ACCEPTED COMPONENTS",
        manifest.get(
            "components",
            {},
        ),
    )

    failures += verify_group(
        "INACTIVE CANDIDATE COMPONENTS",
        manifest.get(
            "candidate_components",
            {},
        ),
    )

    safety = manifest.get(
        "safety",
        {},
    )

    print()
    print(
        "=== MANIFEST SAFETY DECLARATIONS ==="
    )

    checks = {
        "OANDA practice":
            safety.get(
                "oanda_environment"
            )
            == "practice",

        "Order writes disabled":
            safety.get(
                "order_writes_enabled"
            )
            is False,

        "Order endpoints expected false":
            safety.get(
                "order_endpoints_expected"
            )
            is False,

        "Canonical M005 touch disallowed":
            safety.get(
                "canonical_m005_touch_allowed"
            )
            is False,
    }

    for label, ok in checks.items():
        print(
            f"{label}: "
            f"{'PASS' if ok else 'FAIL'}"
        )

        if not ok:
            failures += 1

    print()
    print("=" * 78)

    if failures:
        print(
            "M006E_FREEZE_MANIFEST: FAIL"
        )
        print(
            "Unexpected source/provenance drift detected."
        )
        print(
            "Failures:",
            failures,
        )
        print("=" * 78)

        raise SystemExit(1)

    print(
        "M006E_FREEZE_MANIFEST: PASS"
    )
    print(
        "All accepted and candidate source hashes "
        "match the recorded provenance manifest."
    )
    print(
        "Network calls: 0"
    )
    print(
        "Trading/order writes: 0"
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

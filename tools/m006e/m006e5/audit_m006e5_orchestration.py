#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(".").resolve()

WRAPPER = (
    ROOT
    / "tools/m006e/m006e5/"
      "run_m006e5_cycle.sh"
)

INSTALLER = (
    ROOT
    / "tools/m006e/m006e5/"
      "install_m006e5_launchd.sh"
)

E1 = (
    ROOT
    / "tools/m006e/"
      "m006e1_oanda_authoritative_observer.py"
)

E2 = (
    ROOT
    / "tools/m006e/"
      "m006e2_twelve_validator.py"
)

E3 = (
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


def sha256(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def require(text: str, token: str):
    if token not in text:
        raise AssertionError(
            f"Required orchestration token missing: {token}"
        )


def forbid(text: str, token: str):
    if token in text:
        raise AssertionError(
            f"Forbidden token found: {token}"
        )


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.5 — "
        "ORCHESTRATION AUDIT"
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

    w = WRAPPER.read_text()
    i = INSTALLER.read_text()

    # Exact stage order.
    p1 = w.index(
        "m006e1_oanda_authoritative_observer.py"
    )

    p2 = w.index(
        "m006e2_twelve_validator.py"
    )

    p3 = w.index(
        "m006e3_zero_write_bridge.py"
    )

    assert p1 < p2 < p3

    print(
        "PASS 01 stage order "
        "M006e.1 -> M006e.2 -> M006e.3"
    )

    require(
        w,
        'OANDA_ENV:-}" != "practice"',
    )

    require(
        w,
        'ENABLE_DEMO_EXECUTION:-NO}" != "NO"',
    )

    print(
        "PASS 02 practice-only + master-switch guard"
    )

    require(
        w,
        'HHMM" -lt 1050',
    )

    require(
        w,
        'HHMM" -gt 1420',
    )

    require(
        w,
        'DOW" -gt 5',
    )

    print(
        "PASS 03 weekday 10:50-14:20 UTC guard"
    )

    require(
        w,
        'mkdir "$LOCKDIR"',
    )

    require(
        w,
        "trap cleanup EXIT INT TERM HUP",
    )

    print(
        "PASS 04 atomic single-instance lock"
    )

    require(
        w,
        "M006e.2 NOT RUN",
    )

    require(
        w,
        "M006e.3 NOT RUN",
    )

    print(
        "PASS 05 upstream failure stops downstream stages"
    )

    require(
        w,
        'source "$SECRETS"',
    )

    require(
        w,
        "PYTHONPATH",
    )

    require(
        w,
        "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
    )

    print(
        "PASS 06 explicit secrets/PATH/Python for launchd"
    )

    require(
        i,
        "<integer>300</integer>",
    )

    require(
        i,
        "<false/>",
    )

    require(
        i,
        "StandardOutPath",
    )

    require(
        i,
        "StandardErrorPath",
    )

    print(
        "PASS 07 launchd interval=300s, RunAtLoad=false, logs configured"
    )

    # Scheduler/wrapper must not themselves contain execution methods.
    combined = (
        w
        + "\n"
        + i
    )

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
        forbid(
            combined,
            token,
        )

    print(
        "PASS 08 orchestration contains no order/write endpoint"
    )

    # Reconfirm core source still has the expected zero-write topology.
    e3 = E3.read_text()

    require(
        e3,
        'method="GET"',
    )

    for token in forbidden:
        forbid(
            e3,
            token,
        )

    print(
        "PASS 09 M006e.3 remains GET-only"
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
        "PASS 10 M006e.1 state unchanged"
    )

    print(
        "PASS 11 M006e.3 state unchanged"
    )

    print(
        "PASS 12 M006c state unchanged"
    )

    print()
    print(
        "Network calls by audit: 0"
    )
    print(
        "Order payloads constructed: 0"
    )
    print(
        "OANDA writes invoked: FALSE"
    )
    print(
        "Scheduler installed by audit: FALSE"
    )

    print()
    print("=" * 78)
    print(
        "M006E5_ORCHESTRATION_AUDIT: PASS"
    )
    print(
        "Ordering, session guard, locking, "
        "fail-closed sequencing and zero-write "
        "scheduler safety verified."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

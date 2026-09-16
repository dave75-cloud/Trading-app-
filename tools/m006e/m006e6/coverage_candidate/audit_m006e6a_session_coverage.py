#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import m006e6a_session_coverage as h


ROOT = Path(".").resolve()

ACTIVE_HEALTH = (
    ROOT
    / "tools/m006e/m006e6/"
      "m006e6_health_report.py"
)

ACTIVE_WRAPPER = (
    ROOT
    / "tools/m006e/m006e5/"
      "run_m006e5_cycle.sh"
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


ACCEPTED_HEALTH_HASH = (
    "32c6baf0a374f699785170e7eb887b0a"
    "1ca3e9b6b6ec2f71f32e480be212362b"
)

ACCEPTED_WRAPPER_HASH = (
    "a5780b27af2d550a47d9163ece6e6db"
    "81e1f8e769ff13c8190fa8565743e036e"
)


def sha(path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def dt(s):
    return datetime.fromisoformat(
        s
    ).replace(
        tzinfo=timezone.utc
    )


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.6a — "
        "SESSION-COVERAGE AUDIT"
    )
    print("=" * 78)

    health0 = sha(
        ACTIVE_HEALTH
    )

    wrapper0 = sha(
        ACTIVE_WRAPPER
    )

    e10 = sha(
        E1_STATE
    )

    e30 = sha(
        E3_STATE
    )

    assert (
        health0
        == ACCEPTED_HEALTH_HASH
    )

    assert (
        wrapper0
        == ACCEPTED_WRAPPER_HASH
    )

    print(
        "PASS 01 accepted M006e.6 and M006e.5 hashes preserved"
    )

    # Before session.
    now = dt(
        "2026-09-01T02:30:00"
    )

    phase, start, end = (
        h.session_phase(
            now
        )
    )

    r = h.evaluate(
        now,
        phase,
        start,
        end,
        [],
        {},
        None,
    )

    assert (
        r["verdict"]
        == "NOT_DUE"
    )

    print(
        "PASS 02 pre-window zero cycles is NOT_DUE"
    )

    # Healthy active session.
    now = dt(
        "2026-09-01T12:00:00"
    )

    phase, start, end = (
        h.session_phase(
            now
        )
    )

    expected = h.expected_cycles(
        now,
        start,
        end,
    )

    logs = [
        {
            "status":
                "PASS"
        }
        for _ in range(
            expected
        )
    ]

    wm = {
        pair:
            now
            - timedelta(
                minutes=5
            )
        for pair in [
            "AUDUSD",
            "EURUSD",
            "GBPUSD",
            "USDJPY",
        ]
    }

    r = h.evaluate(
        now,
        phase,
        start,
        end,
        logs,
        wm,
        now
        - timedelta(
            minutes=5
        ),
    )

    assert (
        r["verdict"]
        == "CLEAN"
    )

    print(
        "PASS 03 healthy active-session coverage => CLEAN"
    )

    # Zero active cycles after 30 min.
    now = dt(
        "2026-09-01T11:20:00"
    )

    phase, start, end = (
        h.session_phase(
            now
        )
    )

    r = h.evaluate(
        now,
        phase,
        start,
        end,
        [],
        wm,
        now,
    )

    assert (
        r["verdict"]
        == "ALERT"
    )

    assert any(
        "no orchestration cycles"
        in text
        for _, text
        in r["issues"]
    )

    print(
        "PASS 04 zero active-window cycles => ALERT"
    )

    # Cycles but no PASS.
    logs = [
        {
            "status":
                "SKIP"
        }
        for _ in range(6)
    ]

    r = h.evaluate(
        now,
        phase,
        start,
        end,
        logs,
        wm,
        now,
    )

    assert (
        r["verdict"]
        == "ALERT"
    )

    assert any(
        "zero PASS"
        in text
        for _, text
        in r["issues"]
    )

    print(
        "PASS 05 cycles with zero PASS => ALERT"
    )

    # Coverage warning.
    expected = h.expected_cycles(
        now,
        start,
        end,
    )

    observed = max(
        1,
        int(
            expected * 0.70
        ),
    )

    logs = [
        {
            "status":
                "PASS"
        }
        for _ in range(
            observed
        )
    ]

    r = h.evaluate(
        now,
        phase,
        start,
        end,
        logs,
        wm,
        now,
    )

    assert (
        r["verdict"]
        in {
            "WARN",
            "ALERT",
        }
    )

    print(
        "PASS 06 materially low cycle coverage is surfaced"
    )

    # Stale watermark.
    logs = [
        {
            "status":
                "PASS"
        }
        for _ in range(
            h.expected_cycles(
                now,
                start,
                end,
            )
        )
    ]

    stale_wm = {
        "AUDUSD":
            now
            - timedelta(
                minutes=40
            ),
        "EURUSD":
            now
            - timedelta(
                minutes=5
            ),
        "GBPUSD":
            now
            - timedelta(
                minutes=5
            ),
        "USDJPY":
            now
            - timedelta(
                minutes=5
            ),
    }

    r = h.evaluate(
        now,
        phase,
        start,
        end,
        logs,
        stale_wm,
        now,
    )

    assert (
        r["verdict"]
        == "ALERT"
    )

    assert any(
        "AUDUSD observer watermark"
        in text
        for _, text
        in r["issues"]
    )

    print(
        "PASS 07 stale observer watermark => ALERT"
    )

    # Stale bridge.
    r = h.evaluate(
        now,
        phase,
        start,
        end,
        logs,
        wm,
        now
        - timedelta(
            minutes=40
        ),
    )

    assert (
        r["verdict"]
        == "ALERT"
    )

    assert any(
        "bridge last-run stale"
        in text
        for _, text
        in r["issues"]
    )

    print(
        "PASS 08 stale bridge last-run => ALERT"
    )

    # Explicit FAIL.
    logs = [
        {
            "status":
                "PASS"
        }
        for _ in range(10)
    ]

    logs.append(
        {
            "status":
                "FAIL"
        }
    )

    r = h.evaluate(
        now,
        phase,
        start,
        end,
        logs,
        wm,
        now,
    )

    assert (
        r["verdict"]
        == "ALERT"
    )

    print(
        "PASS 09 orchestration FAIL => ALERT"
    )

    # Weekend.
    now = dt(
        "2026-09-05T12:00:00"
    )

    phase, start, end = (
        h.session_phase(
            now
        )
    )

    r = h.evaluate(
        now,
        phase,
        start,
        end,
        [],
        {},
        None,
    )

    assert (
        r["verdict"]
        == "NOT_DUE"
    )

    print(
        "PASS 10 weekend zero cycles is NOT_DUE"
    )

    source = Path(
        "tools/m006e/m006e6/coverage_candidate/"
        "m006e6a_session_coverage.py"
    ).read_text()

    forbidden = [
        "urllib.",
        "requests.",
        "http://",
        "https://",
        "/orders",
        "launchctl",
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
    ]

    for token in forbidden:
        assert (
            token not in source
        ), token

    print(
        "PASS 11 candidate has no network/order/scheduler capability"
    )

    assert (
        sha(ACTIVE_HEALTH)
        == health0
    )

    assert (
        sha(ACTIVE_WRAPPER)
        == wrapper0
    )

    assert (
        sha(E1_STATE)
        == e10
    )

    assert (
        sha(E3_STATE)
        == e30
    )

    print(
        "PASS 12 active M006e.6 unchanged"
    )

    print(
        "PASS 13 active M006e.5 unchanged"
    )

    print(
        "PASS 14 M006e.1 prospective state unchanged"
    )

    print(
        "PASS 15 M006e.3 prospective state unchanged"
    )

    print()
    print(
        "Network calls: 0"
    )

    print(
        "Trading/order writes: 0"
    )

    print(
        "Candidate promoted: FALSE"
    )

    print()
    print("=" * 78)
    print(
        "M006E6A_SESSION_COVERAGE_AUDIT: PASS"
    )

    print(
        "Active-session coverage, stale watermark, "
        "bridge freshness and fail/skip conditions verified."
    )

    print("=" * 78)


if __name__ == "__main__":
    main()

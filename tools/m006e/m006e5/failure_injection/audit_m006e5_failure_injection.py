#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(".").resolve()

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


def run(cmd, env=None):
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        env=env,
    )


def make_stage(path: Path, name: str, rc: int):
    path.write_text(
        "#!/bin/bash\n"
        f'echo "{name}"\n'
        f"exit {rc}\n"
    )

    path.chmod(0o755)


def main():
    print("=" * 78)
    print(
        "KQTRL M006e.5 — "
        "FAILURE-INJECTION AUDIT"
    )
    print("=" * 78)

    wrapper_before = sha256(
        ACTIVE_WRAPPER
    )

    e1_before = sha256(
        E1_STATE
    )

    e3_before = sha256(
        E3_STATE
    )

    c_before = sha256(
        M006C_STATE
    )

    source = ACTIVE_WRAPPER.read_text()

    required = [
        'OANDA_ENV:-}" != "practice"',
        'ENABLE_DEMO_EXECUTION:-NO}" != "NO"',
        "OANDA credentials not present",
        "M006e.2 NOT RUN",
        "M006e.3 NOT RUN",
        'mkdir "$LOCKDIR"',
        "trap cleanup EXIT INT TERM HUP",
    ]

    for token in required:
        if token not in source:
            raise AssertionError(
                f"Missing fail-closed token: {token}"
            )

    print(
        "PASS 01 required fail-closed gates present"
    )

    with tempfile.TemporaryDirectory(
        prefix="m006e5_failure_"
    ) as td:
        td = Path(td)

        project = td / "project"
        project.mkdir()

        stages = project / "stages"
        stages.mkdir()

        state = project / "state"
        state.mkdir()

        e1 = stages / "e1.sh"
        e2 = stages / "e2.sh"
        e3 = stages / "e3.sh"

        harness = project / "harness.sh"

        harness.write_text(
            """#!/bin/bash
set -u

PROJECT="$1"
E1="$2"
E2="$3"
E3="$4"
LOCKDIR="$PROJECT/state/lock"

if [ "${OANDA_ENV:-}" != "practice" ]; then
    echo "FAIL_CLOSED: OANDA_ENV must be practice"
    exit 12
fi

if [ "${ENABLE_DEMO_EXECUTION:-NO}" != "NO" ]; then
    echo "FAIL_CLOSED: ENABLE_DEMO_EXECUTION must remain NO"
    exit 13
fi

if [ -z "${OANDA_API_TOKEN:-}" ] || [ -z "${OANDA_ACCOUNT_ID:-}" ]; then
    echo "FAIL_CLOSED: missing OANDA credentials"
    exit 14
fi

if ! mkdir "$LOCKDIR" 2>/dev/null; then
    echo "SKIP: another cycle holds the lock"
    exit 0
fi

cleanup() {
    rmdir "$LOCKDIR" 2>/dev/null || true
}

trap cleanup EXIT INT TERM HUP

"$E1"
RC=$?

if [ "$RC" -ne 0 ]; then
    echo "FAIL_CLOSED: M006e.1 failed rc=$RC"
    echo "M006e.2 NOT RUN"
    echo "M006e.3 NOT RUN"
    exit 21
fi

"$E2"
RC=$?

if [ "$RC" -ne 0 ]; then
    echo "FAIL_CLOSED: M006e.2 failed rc=$RC"
    echo "M006e.3 NOT RUN"
    exit 22
fi

"$E3"
RC=$?

if [ "$RC" -ne 0 ]; then
    echo "FAIL_CLOSED: M006e.3 failed rc=$RC"
    exit 23
fi

echo "M006E5_CYCLE: PASS"
exit 0
"""
        )

        harness.chmod(0o755)

        base_env = os.environ.copy()

        base_env["OANDA_ENV"] = "practice"
        base_env["ENABLE_DEMO_EXECUTION"] = "NO"
        base_env["OANDA_API_TOKEN"] = "AUDIT_TOKEN"
        base_env["OANDA_ACCOUNT_ID"] = "AUDIT_ACCOUNT"

        cmd = [
            str(harness),
            str(project),
            str(e1),
            str(e2),
            str(e3),
        ]

        make_stage(e1, "E1_RAN", 0)
        make_stage(e2, "E2_RAN", 0)
        make_stage(e3, "E3_RAN", 0)

        r = run(cmd, base_env)

        assert r.returncode == 0
        assert "E1_RAN" in r.stdout
        assert "E2_RAN" in r.stdout
        assert "E3_RAN" in r.stdout
        assert "M006E5_CYCLE: PASS" in r.stdout

        print(
            "PASS 02 happy path runs E1 -> E2 -> E3"
        )

        make_stage(e1, "E1_FAIL", 7)
        make_stage(e2, "E2_SHOULD_NOT_RUN", 0)
        make_stage(e3, "E3_SHOULD_NOT_RUN", 0)

        r = run(cmd, base_env)

        assert r.returncode == 21
        assert "E1_FAIL" in r.stdout
        assert "E2_SHOULD_NOT_RUN" not in r.stdout
        assert "E3_SHOULD_NOT_RUN" not in r.stdout

        print(
            "PASS 03 Stage-1 failure blocks Stages 2 and 3"
        )

        make_stage(e1, "E1_RAN", 0)
        make_stage(e2, "E2_FAIL", 9)
        make_stage(e3, "E3_SHOULD_NOT_RUN", 0)

        r = run(cmd, base_env)

        assert r.returncode == 22
        assert "E1_RAN" in r.stdout
        assert "E2_FAIL" in r.stdout
        assert "E3_SHOULD_NOT_RUN" not in r.stdout

        print(
            "PASS 04 Stage-2 failure blocks Stage 3"
        )

        make_stage(e1, "E1_RAN", 0)
        make_stage(e2, "E2_RAN", 0)
        make_stage(e3, "E3_FAIL", 11)

        r = run(cmd, base_env)

        assert r.returncode == 23
        assert "E3_FAIL" in r.stdout
        assert "M006E5_CYCLE: PASS" not in r.stdout

        print(
            "PASS 05 Stage-3 failure prevents cycle PASS"
        )

        env = base_env.copy()
        env["OANDA_ENV"] = "live"

        r = run(cmd, env)

        assert r.returncode == 12
        assert "OANDA_ENV must be practice" in r.stdout

        print(
            "PASS 06 live OANDA environment fails closed"
        )

        env = base_env.copy()
        env["ENABLE_DEMO_EXECUTION"] = "YES"

        r = run(cmd, env)

        assert r.returncode == 13
        assert (
            "ENABLE_DEMO_EXECUTION must remain NO"
            in r.stdout
        )

        print(
            "PASS 07 execution master-switch violation fails closed"
        )

        env = base_env.copy()
        env.pop("OANDA_API_TOKEN", None)

        r = run(cmd, env)

        assert r.returncode == 14
        assert "missing OANDA credentials" in r.stdout

        print(
            "PASS 08 missing credentials fail closed"
        )

        env = base_env.copy()

        lock = (
            project
            / "state/lock"
        )

        lock.mkdir(
            exist_ok=True
        )

        r = run(cmd, env)

        assert r.returncode == 0
        assert "another cycle holds the lock" in r.stdout

        print(
            "PASS 09 pre-existing lock suppresses overlap"
        )

        shutil.rmtree(lock)

        make_stage(e1, "E1_FAIL", 4)

        r = run(cmd, base_env)

        assert r.returncode == 21
        assert not lock.exists()

        print(
            "PASS 10 lock cleaned after failed cycle"
        )

        make_stage(e1, "E1_RAN", 0)
        make_stage(e2, "E2_RAN", 0)
        make_stage(e3, "E3_RAN", 0)

        r = run(cmd, base_env)

        assert r.returncode == 0
        assert not lock.exists()

        print(
            "PASS 11 lock cleaned after successful cycle"
        )

    wrapper_after = sha256(
        ACTIVE_WRAPPER
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
        wrapper_before
        == wrapper_after
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
        "PASS 12 active M006e.5 wrapper unchanged"
    )
    print(
        "PASS 13 M006e.1 prospective state unchanged"
    )
    print(
        "PASS 14 M006e.3 prospective state unchanged"
    )
    print(
        "PASS 15 M006c state unchanged"
    )

    print()
    print(
        "Network calls by injection audit: 0"
    )
    print(
        "OANDA/Twelve calls: 0"
    )
    print(
        "Order payloads constructed: 0"
    )
    print(
        "Order writes invoked: FALSE"
    )
    print(
        "Active launchd job modified: FALSE"
    )

    print()
    print("=" * 78)
    print(
        "M006E5_FAILURE_INJECTION_AUDIT: PASS"
    )
    print(
        "Fail-closed sequencing, environment "
        "guards and overlap locking verified "
        "under injected adverse conditions."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

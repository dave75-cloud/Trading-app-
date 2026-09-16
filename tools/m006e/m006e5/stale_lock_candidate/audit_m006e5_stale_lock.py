#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(".").resolve()

ACTIVE = (
    ROOT
    / "tools/m006e/m006e5/run_m006e5_cycle.sh"
)

HELPER = (
    ROOT
    / "tools/m006e/m006e5/stale_lock_candidate/"
      "m006e5_stale_lock.sh"
)

CANDIDATE = (
    ROOT
    / "tools/m006e/m006e5/stale_lock_candidate/"
      "run_m006e5_cycle.stale_lock_candidate.sh"
)

E1_STATE = (
    ROOT
    / "data/research_runs/M006E_OANDA_AUTHORITATIVE/"
      "state/observer_state.json"
)

E3_STATE = (
    ROOT
    / "data/research_runs/M006E_OANDA_AUTHORITATIVE/"
      "bridge/state/bridge_state.json"
)

C_STATE = (
    ROOT
    / "data/research_runs/M006_PRACTICE_EXECUTION/"
      "signal_order_bridge/state/bridge_state.json"
)


ACCEPTED_ACTIVE_HASH = (
    "a5780b27af2d550a47d9163ece6e6db"
    "81e1f8e769ff13c8190fa8565743e036e"
)


def sha(path: Path):
    if not path.exists():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def shell(script: str, env=None):
    return subprocess.run(
        ["/bin/bash", "-c", script],
        text=True,
        capture_output=True,
        env=env,
    )


def main():
    print("=" * 78)
    print("KQTRL M006e.5a — STALE-LOCK RESILIENCE AUDIT")
    print("=" * 78)

    active0 = sha(ACTIVE)
    e10 = sha(E1_STATE)
    e30 = sha(E3_STATE)
    c0 = sha(C_STATE)

    assert active0 == ACCEPTED_ACTIVE_HASH
    print("PASS 01 active accepted wrapper hash preserved")

    subprocess.run(
        ["/bin/bash", "-n", str(HELPER)],
        check=True,
    )

    subprocess.run(
        ["/bin/bash", "-n", str(CANDIDATE)],
        check=True,
    )

    print("PASS 02 helper and candidate shell syntax")

    helper_source = HELPER.read_text()
    candidate_source = CANDIDATE.read_text()

    assert "LOCK_STALE_SECONDS" in helper_source
    assert "kill -0" in helper_source
    assert "run_m006e5_cycle.sh" in helper_source
    assert 'mv "$LOCKDIR" "$_quarantine"' in helper_source
    assert "m006e5_release_lock" in helper_source

    assert "m006e5_acquire_lock" in candidate_source
    assert "m006e5_release_lock" in candidate_source
    assert "m006e5_stale_lock.sh" in candidate_source

    print("PASS 03 candidate integrates exact stale-lock helper")

    with tempfile.TemporaryDirectory(
        prefix="m006e5_stale_lock_"
    ) as td:
        td = Path(td)
        lock = td / "lock"

        env = os.environ.copy()

        # Test helper in a subprocess so $$ ownership semantics are real.
        def run_case(body: str):
            script = f'''
set -u
LOCKDIR="{lock}"
LOCK_STALE_SECONDS=900
. "{HELPER}"
{body}
'''
            return shell(script, env)

        # Clean acquire + release.
        r = run_case(
            '''
m006e5_acquire_lock || exit 31
[ -f "$LOCKDIR/pid" ] || exit 32
[ -f "$LOCKDIR/created_epoch" ] || exit 33
m006e5_release_lock
[ ! -d "$LOCKDIR" ] || exit 34
'''
        )

        assert r.returncode == 0, (r.stdout, r.stderr)
        print("PASS 04 clean lock acquisition and owner-aware release")

        # Recent orphan must NOT be reclaimed.
        lock.mkdir()
        (lock / "pid").write_text("99999999\n")
        (lock / "created_epoch").write_text(
            f"{int(time.time())}\n"
        )

        r = run_case(
            '''
if m006e5_acquire_lock; then
    exit 41
fi
[ -d "$LOCKDIR" ] || exit 42
'''
        )

        assert r.returncode == 0, (r.stdout, r.stderr)
        assert "recent orphan/uncertain" in r.stdout

        print("PASS 05 recent dead-owner lock fails closed")

        # Make it stale.
        old = int(time.time()) - 3600

        (lock / "created_epoch").write_text(
            f"{old}\n"
        )

        r = run_case(
            '''
m006e5_acquire_lock || exit 51
grep -q "^$$$" "$LOCKDIR/pid" || exit 52
m006e5_release_lock
[ ! -d "$LOCKDIR" ] || exit 53
'''
        )

        assert r.returncode == 0, (r.stdout, r.stderr)
        assert "stale lock recovered" in r.stdout

        print("PASS 06 old dead-owner lock recovered safely")

        # Unknown-age lock must fail closed.
        lock.mkdir()
        (lock / "pid").write_text("99999999\n")

        # Deliberately force future mtime so helper returns unknown age.
        future = time.time() + 3600
        os.utime(
            lock,
            (future, future),
        )

        r = run_case(
            '''
if m006e5_acquire_lock; then
    exit 61
fi
'''
        )

        assert r.returncode == 0, (r.stdout, r.stderr)
        assert "age unknown" in r.stdout

        print("PASS 07 unknown/future lock age fails closed")

        # Clean up test lock.
        for child in lock.iterdir():
            child.unlink()
        lock.rmdir()

        # Owner-aware release must not remove someone else's lock.
        lock.mkdir()
        (lock / "pid").write_text("123456789\n")
        (lock / "created_epoch").write_text(
            f"{int(time.time())}\n"
        )

        r = run_case(
            '''
m006e5_release_lock
[ -d "$LOCKDIR" ] || exit 71
'''
        )

        assert r.returncode == 0, (r.stdout, r.stderr)
        assert "owner changed" in r.stdout

        print("PASS 08 release cannot remove another owner's lock")

        for child in lock.iterdir():
            child.unlink()
        lock.rmdir()

        # Live matching-owner simulation by overriding helper function.
        lock.mkdir()
        (lock / "pid").write_text(f"{os.getpid()}\n")
        (lock / "created_epoch").write_text(
            f"{int(time.time()) - 3600}\n"
        )

        r = run_case(
            f'''
m006e5_lock_owner_command() {{
    echo "/bin/bash {ACTIVE}"
}}

if m006e5_acquire_lock; then
    exit 81
fi
'''
        )

        assert r.returncode == 0, (r.stdout, r.stderr)
        assert "live matching owner" in r.stdout

        print("PASS 09 live matching owner is never reclaimed")

        for child in lock.iterdir():
            child.unlink()
        lock.rmdir()

    # Source safety checks.
    combined = helper_source + "\n" + candidate_source

    forbidden = [
        "curl ",
        "wget ",
        "requests.",
        "urllib.",
        "/orders",
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
    ]

    for token in forbidden:
        assert token not in combined, token

    print("PASS 10 candidate lock layer has no network/order capability")

    assert sha(ACTIVE) == active0
    assert sha(E1_STATE) == e10
    assert sha(E3_STATE) == e30
    assert sha(C_STATE) == c0

    print("PASS 11 active M006e.5 wrapper unchanged")
    print("PASS 12 M006e.1 prospective state unchanged")
    print("PASS 13 M006e.3 prospective state unchanged")
    print("PASS 14 M006c state unchanged")

    print()
    print("Network calls by audit: 0")
    print("Trading/order writes: 0")
    print("Active launchd job modified: FALSE")
    print("Candidate promoted: FALSE")

    print()
    print("=" * 78)
    print("M006E5A_STALE_LOCK_AUDIT: PASS")
    print(
        "Old orphan locks recover conservatively; "
        "live, recent and ambiguous locks remain fail-closed."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()

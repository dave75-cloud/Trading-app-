#!/bin/bash
set -u

PROJECT="$HOME/Projects/Trading-app-"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="$PROJECT/tools/m006e"

SECRETS="$HOME/.kqtrl/m006_secrets.sh"

ROOT="$PROJECT/data/research_runs/M006E_OANDA_AUTHORITATIVE"
ORCH="$ROOT/orchestration"
LOGDIR="$ORCH/logs"
LOCKDIR="$ORCH/m006e5_cycle.lock"

mkdir -p "$LOGDIR"

RUN_ID="$(date -u '+%Y%m%dT%H%M%SZ')"
LOG="$LOGDIR/cycle_${RUN_ID}.log"

exec >>"$LOG" 2>&1

echo "=============================================================================="
echo "KQTRL M006e.5 — PROSPECTIVE ZERO-WRITE ORCHESTRATION"
echo "=============================================================================="
echo "Run UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "Project: $PROJECT"
echo

if [ ! -x "$PYTHON" ]; then
    echo "FAIL_CLOSED: Python executable missing: $PYTHON"
    exit 10
fi

if [ ! -f "$SECRETS" ]; then
    echo "FAIL_CLOSED: secrets file missing"
    exit 11
fi

# shellcheck disable=SC1090
source "$SECRETS"

if [ "${OANDA_ENV:-}" != "practice" ]; then
    echo "FAIL_CLOSED: OANDA_ENV must be practice"
    exit 12
fi

if [ "${ENABLE_DEMO_EXECUTION:-NO}" != "NO" ]; then
    echo "FAIL_CLOSED: ENABLE_DEMO_EXECUTION must remain NO"
    exit 13
fi

if [ -z "${OANDA_API_TOKEN:-}" ] || [ -z "${OANDA_ACCOUNT_ID:-}" ]; then
    echo "FAIL_CLOSED: OANDA credentials not present"
    exit 14
fi

# ---------------------------------------------------------------------------
# UTC operating window
#
# Weekdays only.
# Start 10:50 UTC to establish a clean pre-session cadence.
# Continue through 14:20 UTC so delayed AUDUSD exits and retry-pending
# risk-reducing actions can be observed after the 14:00 session boundary.
# ---------------------------------------------------------------------------

DOW="$(date -u '+%u')"
HHMM="$(date -u '+%H%M')"

if [ "$DOW" -gt 5 ]; then
    echo "SKIP: weekend UTC day=$DOW"
    exit 0
fi

if [ "$HHMM" -lt 1050 ] || [ "$HHMM" -gt 1420 ]; then
    echo "SKIP: outside M006e.5 UTC operating window; HHMM=$HHMM"
    exit 0
fi

# ---------------------------------------------------------------------------
# Single-instance lock.
# mkdir is atomic and available on macOS without requiring flock.
# ---------------------------------------------------------------------------

if ! mkdir "$LOCKDIR" 2>/dev/null; then
    echo "SKIP: another M006e.5 cycle holds the lock"
    exit 0
fi

cleanup() {
    rmdir "$LOCKDIR" 2>/dev/null || true
}

trap cleanup EXIT INT TERM HUP

cd "$PROJECT" || {
    echo "FAIL_CLOSED: cannot cd to project"
    exit 15
}

echo "LOCK: acquired"
echo

echo "=== STAGE 1/3 — M006e.1 OANDA AUTHORITATIVE OBSERVER ==="

"$PYTHON" \
    tools/m006e/m006e1_oanda_authoritative_observer.py

RC=$?

if [ "$RC" -ne 0 ]; then
    echo
    echo "FAIL_CLOSED: M006e.1 failed rc=$RC"
    echo "M006e.2 NOT RUN"
    echo "M006e.3 NOT RUN"
    exit 21
fi

echo
echo "PASS: M006e.1"
echo

echo "=== STAGE 2/3 — M006e.2 TWELVE VALIDATOR ==="

"$PYTHON" \
    tools/m006e/m006e2_twelve_validator.py

RC=$?

if [ "$RC" -ne 0 ]; then
    echo
    echo "FAIL_CLOSED: M006e.2 failed rc=$RC"
    echo "M006e.3 NOT RUN"
    exit 22
fi

echo
echo "PASS: M006e.2"
echo

echo "=== STAGE 3/3 — M006e.3 ZERO-WRITE BRIDGE ==="

"$PYTHON" \
    tools/m006e/m006e3_zero_write_bridge.py

RC=$?

if [ "$RC" -ne 0 ]; then
    echo
    echo "FAIL_CLOSED: M006e.3 failed rc=$RC"
    exit 23
fi

echo
echo "PASS: M006e.3"
echo
echo "=============================================================================="
echo "M006E5_CYCLE: PASS"
echo "Order writing capability: NONE"
echo "OANDA environment: practice"
echo "=============================================================================="

exit 0

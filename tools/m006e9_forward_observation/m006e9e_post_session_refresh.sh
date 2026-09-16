#!/bin/bash
set -euo pipefail

# M006e.9e — Post-Session Observation Refresh
#
# Usage:
#   tools/m006e9_forward_observation/m006e9e_post_session_refresh.sh YYYY-MM-DD
#
# Preconditions:
#   - session has completed
#   - anomalies have been reviewed
#   - human-reviewed disposition already exists
#
# This script:
#   - verifies frozen M006e.9 analytics
#   - creates the date's M006e.9a session extract
#   - refreshes cumulative ledger
#   - displays graduation status
#   - refreshes formal report
#   - creates immutable dated snapshots
#
# It does NOT:
#   - classify failures
#   - create a reviewed disposition
#   - touch the active M006e trading stack
#   - contact OANDA/Twelve
#   - submit orders
#   - promote the system

if [ "$#" -ne 1 ]; then
    echo "USAGE: $0 YYYY-MM-DD"
    exit 2
fi

DAY="$1"

if ! echo "$DAY" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
    echo "REFUSED: date must be YYYY-MM-DD"
    exit 2
fi

ROOT="data/research_runs/M006E_FORWARD_OBSERVATION"
TOOLS="tools/m006e9_forward_observation"

SESSION_FILE="$ROOT/sessions/m006e9a_${DAY}.json"
DISPOSITION_FILE="$ROOT/dispositions/session_disposition_${DAY}.json"

LEDGER_JSON="$ROOT/ledger/m006e9b_cumulative_ledger.json"
LEDGER_CSV="$ROOT/ledger/m006e9b_sessions.csv"
REPORT="$ROOT/reports/M006e_Forward_Observation_Report.md"

LEDGER_HISTORY="$ROOT/ledger/history/m006e9b_through_${DAY}.json"
CSV_HISTORY="$ROOT/ledger/history/m006e9b_sessions_through_${DAY}.csv"
REPORT_HISTORY="$ROOT/reports/history/M006e_Forward_Observation_Report_through_${DAY}.md"

SNAPSHOT_HASH="$ROOT/reports/history/M006e9_snapshot_${DAY}.sha256"

echo "================================================================"
echo "M006e.9e — POST-SESSION OBSERVATION REFRESH"
echo "DAY: $DAY"
echo "================================================================"

echo
echo "=== 1. VERIFY FROZEN ANALYTICS STACK ==="

shasum -a 256 -c \
  "$TOOLS/accepted/M006e9_ANALYTICS_STACK.sha256"

echo
echo "=== 2. VERIFY REVIEWED DISPOSITION EXISTS ==="

BASELINE_HAS_DAY=0

if python3 - "$DAY" <<'PY'
import json
import sys
from pathlib import Path

day = sys.argv[1]

path = Path(
    "data/research_runs/M006E_FORWARD_OBSERVATION/"
    "session_dispositions.json"
)

if not path.exists():
    raise SystemExit(1)

obj = json.loads(path.read_text())

raise SystemExit(
    0 if day in (obj.get("sessions") or {}) else 1
)
PY
then
    BASELINE_HAS_DAY=1
fi

if [ "$BASELINE_HAS_DAY" -eq 0 ] && [ ! -f "$DISPOSITION_FILE" ]; then
    echo "REFUSED:"
    echo "No reviewed disposition exists for $DAY."
    echo
    echo "Review/classify the session first."
    echo "M006e.9e will not make that decision automatically."
    exit 3
fi

echo "Reviewed disposition: PRESENT"

echo
echo "=== 3. PROTECT AGAINST SESSION-RECORD OVERWRITE ==="

if [ -e "$SESSION_FILE" ]; then
    echo "REFUSED:"
    echo "Session record already exists:"
    echo "  $SESSION_FILE"
    echo
    echo "Append-only evidence policy prevents overwrite."
    exit 4
fi

echo "No existing session record: PASS"

echo
echo "=== 4. PROTECT AGAINST HISTORY-SNAPSHOT OVERWRITE ==="

for FILE in \
    "$LEDGER_HISTORY" \
    "$CSV_HISTORY" \
    "$REPORT_HISTORY" \
    "$SNAPSHOT_HASH"
do
    if [ -e "$FILE" ]; then
        echo "REFUSED:"
        echo "Historical snapshot already exists:"
        echo "  $FILE"
        exit 5
    fi
done

echo "No existing dated snapshots: PASS"

echo
echo "=== 5. EXTRACT ACCEPTED SESSION EVIDENCE ==="

python3 \
  "$TOOLS/m006e9a_session_extractor.py" \
  --date "$DAY" \
  --compact \
  --write

chmod 444 \
  "$SESSION_FILE"

echo
echo "=== 6. REFRESH CUMULATIVE LEDGER ==="

python3 \
  "$TOOLS/m006e9b_cumulative_ledger.py" \
  --write

echo
echo "=== 7. RUN GRADUATION MONITOR ==="

python3 \
  "$TOOLS/m006e9c_graduation_monitor.py"

echo
echo "=== 8. REFRESH FORMAL REPORT ==="

python3 \
  "$TOOLS/m006e9d_forward_observation_report.py" \
  --write

echo
echo "=== 9. CREATE IMMUTABLE DAILY SNAPSHOTS ==="

mkdir -p \
  "$ROOT/ledger/history" \
  "$ROOT/reports/history"

cp "$LEDGER_JSON" "$LEDGER_HISTORY"
cp "$LEDGER_CSV" "$CSV_HISTORY"
cp "$REPORT" "$REPORT_HISTORY"

chmod 444 \
  "$LEDGER_HISTORY" \
  "$CSV_HISTORY" \
  "$REPORT_HISTORY"

echo
echo "=== 10. HASH DAILY SNAPSHOT ==="

shasum -a 256 \
  "$SESSION_FILE" \
  "$LEDGER_HISTORY" \
  "$CSV_HISTORY" \
  "$REPORT_HISTORY" \
  > "$SNAPSHOT_HASH"

chmod 444 \
  "$SNAPSHOT_HASH"

cat "$SNAPSHOT_HASH"

echo
echo "================================================================"
echo "M006e.9e REFRESH COMPLETE"
echo "DAY: $DAY"
echo "TRADING STACK MODIFIED: FALSE"
echo "AUTOMATIC PROMOTION: NONE"
echo "================================================================"

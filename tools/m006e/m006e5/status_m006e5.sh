#!/bin/bash

PROJECT="$HOME/Projects/Trading-app-"
LABEL="com.kqtrl.m006e5.orchestrator"
ROOT="$PROJECT/data/research_runs/M006E_OANDA_AUTHORITATIVE"
LOGDIR="$ROOT/orchestration/logs"

echo "KQTRL M006e.5 — STATUS"
echo "=============================================================================="

echo
echo "launchd:"
launchctl list 2>/dev/null | grep "$LABEL" || echo "  not loaded"

echo
echo "Latest orchestration log:"

LATEST="$(ls -1t "$LOGDIR"/cycle_*.log 2>/dev/null | head -1)"

if [ -n "${LATEST:-}" ]; then
    echo "  $LATEST"
    echo
    tail -80 "$LATEST"
else
    echo "  none"
fi

echo
echo "M006e.1 observer:"
python3 - <<'PY'
from pathlib import Path
import json

p = Path(
    "data/research_runs/"
    "M006E_OANDA_AUTHORITATIVE/"
    "state/observer_state.json"
)

if not p.exists():
    print("  state missing")
else:
    d = json.loads(p.read_text())

    print("  authority:", d.get("authority"))
    print("  initialized:", d.get("initialized_at_utc"))

    for pair, ts in d.get("watermarks", {}).items():
        print(f"  {pair}: {ts}")
PY

echo
echo "M006e.3 bridge:"
python3 - <<'PY'
from pathlib import Path
import json

p = Path(
    "data/research_runs/"
    "M006E_OANDA_AUTHORITATIVE/"
    "bridge/state/bridge_state.json"
)

if not p.exists():
    print("  state missing")
else:
    d = json.loads(p.read_text())

    print("  initialized:", d.get("initialized_at_utc"))
    print("  last run:", d.get("last_run_utc"))
    print("  processed IDs:", len(d.get("processed_event_ids", [])))
    print("  proposal count:", d.get("proposal_count"))

    print("  virtual positions:")

    for pair, st in d.get("virtual_positions", {}).items():
        pos = int(st.get("position", 0))
        name = {
            -1: "short",
             0: "flat",
             1: "long",
        }.get(pos, str(pos))

        print(
            f"    {pair}: {name} "
            f"allocation_x={st.get('allocation_x')}"
        )
PY

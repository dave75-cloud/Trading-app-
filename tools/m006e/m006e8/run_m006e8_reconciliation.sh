#!/bin/bash
set -eu

PROJECT="$HOME/Projects/Trading-app-"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="$PROJECT/tools/m006e/m006e8"

cd "$PROJECT"

DAY="${1:-$(date -u '+%Y-%m-%d')}"

OUTDIR="$PROJECT/data/research_runs/M006E_OANDA_AUTHORITATIVE/reconciliation"

mkdir -p "$OUTDIR"

STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"

"$PYTHON" \
  tools/m006e/m006e8/m006e8_reconciliation_timeline.py \
  --day "$DAY" \
  --json-out "$OUTDIR/m006e8_${DAY}_${STAMP}.json" \
  --csv-out "$OUTDIR/m006e8_${DAY}_${STAMP}.csv"

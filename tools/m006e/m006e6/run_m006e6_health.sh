#!/bin/bash
set -eu

PROJECT="$HOME/Projects/Trading-app-"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

cd "$PROJECT"

DAY="${1:-$(date -u '+%Y-%m-%d')}"

OUTDIR="$PROJECT/data/research_runs/M006E_OANDA_AUTHORITATIVE/health_reports"

mkdir -p "$OUTDIR"

STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"

OUT="$OUTDIR/m006e6_${DAY}_${STAMP}.json"

"$PYTHON" \
  tools/m006e/m006e6/m006e6_health_report.py \
  --day "$DAY" \
  --json-out "$OUT"

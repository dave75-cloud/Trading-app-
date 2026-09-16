#!/bin/bash
set -eu

PROJECT="$HOME/Projects/Trading-app-"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="$PROJECT/tools/m006e/m006e6/coverage_candidate"

cd "$PROJECT"

OUTDIR="$PROJECT/data/research_runs/M006E_OANDA_AUTHORITATIVE/health_reports"

STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"

"$PYTHON" \
  tools/m006e/m006e6/coverage_candidate/m006e6a_session_coverage.py \
  --json-out \
  "$OUTDIR/m006e6a_coverage_${STAMP}.json"

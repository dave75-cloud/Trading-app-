#!/bin/bash
set -eu

PROJECT="$HOME/Projects/Trading-app-"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="$PROJECT/tools/m006e:$PROJECT/tools/m006e/m006e7"

cd "$PROJECT"

DAY="${1:-}"

OUTDIR="$PROJECT/data/research_runs/M006E_OANDA_AUTHORITATIVE/provider_path_diagnostics"

mkdir -p "$OUTDIR"

STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"

if [ -n "$DAY" ]; then
    "$PYTHON" \
      tools/m006e/m006e7/m006e7_provider_path_diagnostics.py \
      --day "$DAY" \
      --json-out "$OUTDIR/m006e7_${DAY}_${STAMP}.json" \
      --csv-out "$OUTDIR/m006e7_${DAY}_${STAMP}.csv"
else
    "$PYTHON" \
      tools/m006e/m006e7/m006e7_provider_path_diagnostics.py \
      --json-out "$OUTDIR/m006e7_all_${STAMP}.json" \
      --csv-out "$OUTDIR/m006e7_all_${STAMP}.csv"
fi

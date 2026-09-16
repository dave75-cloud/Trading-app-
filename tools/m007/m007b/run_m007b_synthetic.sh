#!/bin/bash
set -eu

PROJECT="$HOME/Projects/Trading-app-"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="$PROJECT/tools/m007/m007b"

cd "$PROJECT"

OUTDIR="$PROJECT/data/research_runs/M007_ZERO_WRITE/order_construction"

mkdir -p "$OUTDIR"

STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"

"$PYTHON" \
  tools/m007/m007b/m007b_order_request_builder.py \
  --input \
  tools/m007/m007b/synthetic_approved_entry.json \
  --json-out \
  "$OUTDIR/m007b_synthetic_${STAMP}.json"

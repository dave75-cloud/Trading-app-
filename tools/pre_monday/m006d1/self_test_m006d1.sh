#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$HERE/m006d1_policy_engine.py"

echo "=== 1. AGREED ENTRY SHOULD PASS DRY RUN ==="
python3 "$PY" \
  --action entry --pair AUDUSD \
  --oanda-signal 1 --twelve-signal 1 \
  --oanda-vol-ok true --twelve-vol-ok true \
  --oanda-age-min 1 --twelve-age-min 7 --event-age-min 4 \
  --price-divergence-bps 2.0 --polygon-status pass

echo
echo "=== 2. DIRECTION DISAGREEMENT MUST BLOCK ==="
set +e
python3 "$PY" \
  --action entry --pair USDJPY \
  --oanda-signal 1 --twelve-signal 0 \
  --oanda-vol-ok true --twelve-vol-ok false \
  --oanda-age-min 1 --twelve-age-min 7 --event-age-min 4 \
  --price-divergence-bps 2.0 --polygon-status disagree
rc=$?
set -e
[ "$rc" -eq 10 ] || { echo "FAIL: disagreement test did not block"; exit 1; }

echo
echo "=== 3. RISK-REDUCING EXIT MUST NOT BE BLOCKED BY TWELVE ==="
python3 "$PY" \
  --action exit --pair GBPUSD \
  --oanda-signal 0 --twelve-signal 1 \
  --oanda-vol-ok false --twelve-vol-ok true \
  --oanda-age-min 1 --twelve-age-min 9 \
  --polygon-status disagree

echo
echo "M006d.1 SELF-TEST: PASS"

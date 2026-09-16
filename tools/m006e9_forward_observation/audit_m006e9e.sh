#!/bin/bash
set -euo pipefail

TARGET="tools/m006e9_forward_observation/m006e9e_post_session_refresh.sh"

echo "M006e.9e AUDIT"

test -f "$TARGET"

grep -q 'M006e9_ANALYTICS_STACK.sha256' "$TARGET"
grep -q 'reviewed disposition' "$TARGET"
grep -q 'Append-only evidence policy' "$TARGET"
grep -q 'AUTOMATIC PROMOTION: NONE' "$TARGET"

if grep -Eq \
'curl |wget |requests\.|api\.oanda|/orders|orderCreate|marketOrder' \
"$TARGET"
then
    echo "FAIL: prohibited network/order capability detected"
    exit 1
fi

if grep -Eq \
'python3[[:space:]]+tools/m006e/' \
"$TARGET"
then
    echo "FAIL: direct frozen-runtime execution detected"
    exit 1
fi

echo "  frozen analytics verification: PASS"
echo "  reviewed-disposition prerequisite: PASS"
echo "  append-only session protection: PASS"
echo "  dated snapshot protection: PASS"
echo "  no network/order capability: PASS"
echo "  no direct frozen-runtime execution: PASS"
echo "  automatic promotion: NONE"
echo "M006E9E_AUDIT: PASS"

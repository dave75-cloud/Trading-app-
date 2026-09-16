#!/bin/bash
set -euo pipefail
PROJECT="$HOME/Projects/Trading-app-"; cd "$PROJECT"; RUN="$PROJECT/data/research_runs/M005_FORWARD_SHADOW_20260804T120245Z"
echo "KQTRL — M005 DELAYED RECONCILIATION DIAGNOSTIC"; echo "======================================================================"; date
echo "=== LAUNCHD ==="; launchctl list | grep -Ei 'm005.*recon|delayed-reconciliation|polygon' || true
echo "=== PLISTS ==="; for p in "$HOME/Library/LaunchAgents/"*recon*.plist "$HOME/Library/LaunchAgents/"*polygon*.plist; do [ -f "$p" ] || continue; echo "----- $p -----"; cat "$p"; done
echo "=== RECENT RECON/ACCEPT FILES ==="; find "$RUN" -type f \( -iname '*recon*' -o -iname '*accept*' -o -iname '*checkpoint*' \) -exec ls -lT {} \; 2>/dev/null | tail -100 || true
echo "=== POSSIBLE LOGS ==="; find "$RUN" "$PROJECT/logs" -type f \( -iname '*recon*.log' -o -iname '*polygon*.log' -o -iname '*accept*.log' \) -print 2>/dev/null | while read -r f; do echo "----- $f -----"; tail -80 "$f"; done
echo "=== WRAPPERS ==="; grep -RIl --exclude-dir=.git -E 'delayed.recon|acceptance.ledger|reconciliation' "$HOME/.local/bin" "$PROJECT" 2>/dev/null | head -40 || true
echo "READ ONLY: nothing modified."

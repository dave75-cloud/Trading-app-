#!/bin/bash
set -eu

LABEL="com.kqtrl.m006e5.orchestrator"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

if [ -f "$PLIST" ]; then
    launchctl unload "$PLIST" >/dev/null 2>&1 || true
    rm -f "$PLIST"
fi

echo "KQTRL M006e.5 launchd removed"

#!/bin/bash
set -eu

LABEL="com.kqtrl.m006e5.orchestrator"

PROJECT="$HOME/Projects/Trading-app-"
WRAPPER="$PROJECT/tools/m006e/m006e5/run_m006e5_cycle.sh"

PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOGDIR="$PROJECT/data/research_runs/M006E_OANDA_AUTHORITATIVE/orchestration/logs"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$LOGDIR"

if [ ! -x "$WRAPPER" ]; then
    echo "FAIL_CLOSED: wrapper missing or not executable"
    exit 10
fi

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${WRAPPER}</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${PROJECT}</string>

    <key>StartInterval</key>
    <integer>300</integer>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>${LOGDIR}/launchd_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>${LOGDIR}/launchd_stderr.log</string>
</dict>
</plist>
PLIST

plutil -lint "$PLIST"

# Compatible with older macOS launchd as well as newer systems.
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"

echo "KQTRL M006e.5 launchd installed"
echo "Label: $LABEL"
echo "Interval: 300 seconds"
echo "Wrapper: $WRAPPER"
echo "Plist: $PLIST"
echo
echo "No OANDA order-writing capability is installed by this scheduler."

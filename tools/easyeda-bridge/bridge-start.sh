#!/usr/bin/env bash
# Start the on-demand EDA bridge and wait until /health answers.
# Loading the LaunchAgent alone does not start it (RunAtLoad=false, no KeepAlive),
# so this is the command to run before an EasyEDA session.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL="$REPO/tools/easyeda-bridge"
LABEL="com.hardwarelab.easyeda-bridge"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ ! -f "$PLIST" ]]; then
  echo "no LaunchAgent at $PLIST — run $TOOL/install-agent.sh once first." >&2
  exit 1
fi

if ! launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  echo "loaded $LABEL (on-demand mode: it stays idle until kickstarted)"
fi

launchctl kickstart -k "gui/$(id -u)/$LABEL"
for _ in $(seq 1 20); do
  if curl -s --max-time 2 http://127.0.0.1:49620/health | grep -q easyeda-bridge; then break; fi
  sleep 0.5
done
"$TOOL/bridge-status.sh"

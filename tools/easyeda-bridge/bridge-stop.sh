#!/usr/bin/env bash
# Stop the EDA bridge but keep the LaunchAgent loaded, so bridge-start.sh can
# bring it back without a reinstall. Nothing is started at login.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL="$REPO/tools/easyeda-bridge"
LABEL="com.hardwarelab.easyeda-bridge"

if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl kill TERM "gui/$(id -u)/$LABEL" || true
  sleep 1
  echo "stopped $LABEL (agent stays loaded; start again with bridge-start.sh)"
else
  echo "$LABEL is not loaded"
fi

"$TOOL/bridge-status.sh" || true

#!/usr/bin/env bash
# Install or refresh the EasyEDA bridge LaunchAgent from the repo copy.
# Upstream skill files stay read-only: this runs tools/easyeda-bridge/bridge-server.mjs.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL="$REPO/tools/easyeda-bridge"
LABEL="com.hardwarelab.easyeda-bridge"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UPSTREAM_NODE_MODULES="$REPO/upstreams/easyeda-api-skill/node_modules"
NODE_BIN="$(command -v node)"

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "uninstalled $LABEL (logs kept in $REPO/logs/)"
  exit 0
fi

mkdir -p "$REPO/logs" "$HOME/Library/LaunchAgents"

if [[ ! -e "$TOOL/node_modules" ]]; then
  if [[ -d "$UPSTREAM_NODE_MODULES" ]]; then
    ln -s "$UPSTREAM_NODE_MODULES" "$TOOL/node_modules"
    echo "linked node_modules -> $UPSTREAM_NODE_MODULES"
  else
    (cd "$TOOL" && npm install --omit=dev)
  fi
fi

if [[ -f "$PLIST" ]]; then
  cp "$PLIST" "$PLIST.bak-$(date +%Y%m%d%H%M%S)"
fi
sed -e "s|__NODE__|$NODE_BIN|g" -e "s|__REPO__|$REPO|g" \
  "$TOOL/$LABEL.plist.template" > "$PLIST"
plutil -lint "$PLIST" >/dev/null

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart -k "gui/$(id -u)/$LABEL" 2>/dev/null || true

for _ in $(seq 1 20); do
  if curl -s --max-time 2 http://127.0.0.1:49620/health | grep -q easyeda-bridge; then break; fi
  sleep 0.5
done
"$TOOL/bridge-status.sh"

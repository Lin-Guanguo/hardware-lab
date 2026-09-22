#!/usr/bin/env bash
# Install or refresh the EasyEDA bridge LaunchAgent from the repo copy.
# Upstream skill files stay read-only: this runs tools/easyeda-bridge/bridge-server.mjs.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL="$REPO/tools/easyeda-bridge"
LABEL="com.hardwarelab.easyeda-bridge"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UPSTREAM_NODE_MODULES="$REPO/upstreams/easyeda-api-skill/node_modules"
NO_LOGIN_START=0
QUIET=0
NODE_BIN="$(command -v node || true)"

for arg in "$@"; do
  case "$arg" in
    --no-login-start) NO_LOGIN_START=1 ;;
    --quiet) QUIET=1 ;;
    --uninstall|"") ;;
    *) echo "unknown option: $arg (expected --uninstall, --no-login-start, --quiet)" >&2; exit 2 ;;
  esac
done

if [[ -z "$NODE_BIN" || ! -x "$NODE_BIN" ]]; then
  echo "node not found in PATH. Install Node.js or fix PATH, then re-run." >&2
  exit 1
fi

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "uninstalled $LABEL (logs kept in $REPO/logs/)"
  exit 0
fi

mkdir -p "$REPO/logs" "$HOME/Library/LaunchAgents"

# Refuse to start a second bridge: anything else already on 49620 wins.
PORT_PID="$(lsof -nP -iTCP:49620 -sTCP:LISTEN -t 2>/dev/null | head -1 || true)"
if [[ -n "$PORT_PID" ]] && ! launchctl list "$LABEL" >/dev/null 2>&1; then
  echo "port 49620 is already used by pid $PORT_PID and is not our LaunchAgent." >&2
  echo "Stop that process or run install-agent.sh --uninstall first." >&2
  exit 1
fi

# Rotate launchd logs before they grow without bound (keep one previous file).
for log in "$REPO/logs/easyeda-bridge.out" "$REPO/logs/easyeda-bridge.err"; do
  if [[ -f "$log" ]] && [[ "$(wc -c <"$log")" -gt 5242880 ]]; then
    mv -f "$log" "$log.1"
    : > "$log"
    echo "rotated $log"
  fi
done

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
  ls -1t "$PLIST".bak-* 2>/dev/null | tail -n +3 | while read -r old; do rm -f "$old"; done
fi
sed -e "s|__NODE__|$NODE_BIN|g" -e "s|__REPO__|$REPO|g" \
  "$TOOL/$LABEL.plist.template" > "$PLIST"
if [[ "$NO_LOGIN_START" == "1" ]]; then
  plutil -replace RunAtLoad -bool false "$PLIST"
fi
if [[ "$QUIET" == "1" ]]; then
  plutil -insert EnvironmentVariables.EDA_BRIDGE_QUIET -string 1 "$PLIST" 2>/dev/null || plutil -replace EnvironmentVariables.EDA_BRIDGE_QUIET -string 1 "$PLIST"
fi
plutil -lint "$PLIST" >/dev/null

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
sleep 1
if ! launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null; then
  # launchd can race a just-removed job; one retry after a short pause
  sleep 2
  launchctl bootstrap "gui/$(id -u)" "$PLIST" || true
fi
launchctl kickstart -k "gui/$(id -u)/$LABEL" 2>/dev/null || true

for _ in $(seq 1 20); do
  if curl -s --max-time 2 http://127.0.0.1:49620/health | grep -q easyeda-bridge; then break; fi
  sleep 0.5
done
"$TOOL/bridge-status.sh"

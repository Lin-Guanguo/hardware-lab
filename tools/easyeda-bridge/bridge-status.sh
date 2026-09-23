#!/usr/bin/env bash
# One-shot health check for the EasyEDA bridge LaunchAgent.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LABEL="com.hardwarelab.easyeda-bridge"
PORT="${EDA_BRIDGE_PORT:-49620}"
OUT="$REPO/logs/easyeda-bridge.out"
ERR="$REPO/logs/easyeda-bridge.err"

echo "== $LABEL =="
launchctl list | grep -i "$LABEL" || echo "job: not loaded"
PID="$(pgrep -f 'tools/easyeda-bridge/bridge-server.mjs' | head -1 || true)"
if [[ -n "${PID:-}" ]]; then ps -o pid,etime,%cpu,command -p "$PID" | tail -1; else echo "process: not running"; fi

echo "-- health --"
HEALTH="$(curl -s --max-time 3 "http://127.0.0.1:$PORT/health" || true)"
echo "${HEALTH:-no response}"
echo "-- eda windows --"
curl -s --max-time 3 "http://127.0.0.1:$PORT/eda-windows" || echo "no response"
echo
echo "-- log stats --"
echo "crashes (ERR_HTTP_HEADERS_SENT): $(grep -c 'ERR_HTTP_HEADERS_SENT' "$ERR" 2>/dev/null || echo 0)"
echo "reconnects (New eda connection): $(grep -c 'New eda connection' "$OUT" 2>/dev/null || echo 0)"
ls -l "$OUT" "$ERR" 2>/dev/null | awk '{print $5, $9}'
if [[ -z "${HEALTH:-}" ]] || ! echo "$HEALTH" | grep -q '"service":"easyeda-bridge"'; then
  echo "verdict: bridge down (on-demand mode: start it with tools/easyeda-bridge/bridge-start.sh)"
elif echo "$HEALTH" | grep -q '"edaConnected":true'; then
  echo "verdict: bridge up and EDA connected"
else
  echo "verdict: bridge up but no EDA window - open EasyEDA and check the Run API Gateway extension"
fi

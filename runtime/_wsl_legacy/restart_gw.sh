#!/usr/bin/env bash
# Force-restart the Hermes gateway. Prefers the systemd --user service (G18); falls
# back to the manual kill+relaunch if no unit is installed. Safe to run by hand.
export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
UNIT=hermes-gateway

if systemctl --user list-unit-files 2>/dev/null | grep -q "^${UNIT}\.service"; then
  echo "=== restarting via systemd ==="
  systemctl --user restart "$UNIT"
  sleep 6
  echo "status: $(systemctl --user is-active "$UNIT")"
  exit 0
fi

echo "=== no systemd unit -> manual restart ==="
pkill -f 'venv/bin/hermes gateway run' 2>/dev/null
sleep 4
setsid bash -lc 'export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"; hermes gateway run > ~/.hermes/logs/gateway.log 2>&1' < /dev/null &
disown
sleep 18
echo "=== gateway procs ==="
pgrep -af 'venv/bin/hermes gateway run' || echo "DOWN"

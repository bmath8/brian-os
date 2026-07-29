#!/usr/bin/env bash
# Ensure the Hermes gateway is running. Idempotent + race-safe.
#
# PREFERRED (G18, 2026-06-17): a systemd --user service `hermes-gateway` (installed
# via `hermes gateway install` + `loginctl enable-linger`). Under systemd the gateway
# runs as `python -m hermes_cli.main gateway run` — which the old pgrep patterns do NOT
# match — so we MUST check systemd here, or we'd spawn a duplicate and cause a Telegram
# 409 conflict. If the unit is installed we defer to systemd entirely.
#
# FALLBACK (no systemd unit): the race-safe manual launch (G16) — liveness must survive
# a recheck (a dying process disappears), and we kill+reap before relaunch so two
# gateways never fight over the bot token.
#
# Prints GW:up / GW:healed / GW:down for callers (watchdog parses this).
export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
UNIT=hermes-gateway

# ---- Preferred: systemd --user service ----
if systemctl --user list-unit-files 2>/dev/null | grep -q "^${UNIT}\.service"; then
  if systemctl --user is-active --quiet "$UNIT"; then echo "GW:up"; exit 0; fi
  systemctl --user start "$UNIT" 2>/dev/null
  sleep 8
  if systemctl --user is-active --quiet "$UNIT"; then echo "GW:healed"; exit 0; fi
  echo "GW:down"; exit 1
fi

# ---- Fallback: manual launch (no systemd unit present) ----
PAT='venv/bin/hermes gateway run'
is_up() {
  local p1 p2
  p1=$(pgrep -f "$PAT" | head -1); [ -n "$p1" ] || return 1
  sleep 3
  p2=$(pgrep -f "$PAT" | head -1); [ -n "$p2" ] || return 1   # vanished -> was dying
  grep -q 'State:[[:space:]]*Z' "/proc/$p2/status" 2>/dev/null && return 1
  return 0
}
if is_up; then echo "GW:up"; exit 0; fi
pkill -f "$PAT" 2>/dev/null
for _ in $(seq 1 12); do pgrep -f "$PAT" >/dev/null || break; sleep 1; done
mkdir -p ~/.hermes/logs
setsid bash -lc 'export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"; hermes gateway run >> ~/.hermes/logs/gateway.log 2>&1' < /dev/null &
disown
sleep 18
if pgrep -f "$PAT" >/dev/null; then echo "GW:healed"; exit 0; else echo "GW:down"; exit 1; fi

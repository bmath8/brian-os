#!/usr/bin/env bash
# One-shot, READ-ONLY fleet health check. Safe to run anytime; changes nothing.
# Usage (from WSL):  bash ~/.hermes/scripts/fleet_status.sh
#        or in repo:  bash runtime/fleet_status.sh
export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
REPO=/mnt/c/Brian/02_Projects/brian-os-fleet
HIP=$(ip route | awk '/default/{print $3}')
echo "================ BRIAN-OS FLEET STATUS  $(date '+%Y-%m-%d %H:%M') ================"

echo "-- Gateway --"
if systemctl --user list-unit-files 2>/dev/null | grep -q '^hermes-gateway\.service'; then
  echo "   systemd hermes-gateway: $(systemctl --user is-active hermes-gateway) (linger: $(loginctl show-user "$USER" 2>/dev/null | sed -n 's/Linger=//p'))"
else
  pgrep -f 'venv/bin/hermes gateway run' >/dev/null && echo "   manual gateway: running" || echo "   gateway: DOWN"
fi
echo "   instances (want 1): $(pgrep -fc 'gateway run')"

echo "-- Ollama / models --"
if curl -s -m 5 "http://$HIP:11434/api/tags" >/dev/null 2>&1; then
  echo "   reachable at $HIP:11434"
  curl -s -m 5 "http://$HIP:11434/api/tags" | grep -o '"name":"[^"]*"' | sed 's/"name":/   - /;s/"//g'
else
  echo "   Ollama UNREACHABLE"
fi

echo "-- Scheduled agents --"
hermes cron list 2>/dev/null | awk '/Name:/{n=$2} /Last run:/{print "   "n": last "$3" "$4}'

echo "-- Host resources --"
if [ -f "$REPO/comms/resource_status.json" ]; then
  python3 -c "import json;r=json.load(open('$REPO/comms/resource_status.json'));print(f\"   RAM {r['ram_free_gb']}GB free ({r['ram_pct']}% used) | commit {r['commit_pct']}% | VRAM {r['vram_used_mb']}/{r['vram_total_mb']}MB\")" 2>/dev/null
fi
echo "   disk C: $(df -h /mnt/c 2>/dev/null | awk 'NR==2{print $4" free"}')"

echo "-- Backup --"
DST=/mnt/c/Brian/Harmony_backup
n=$(find "$DST" -type f 2>/dev/null | wc -l)
newest=$(find "$DST" -type f -printf '%TY-%Tm-%Td %TH:%TM\n' 2>/dev/null | sort -r | head -1)
echo "   Harmony_backup: $n files, newest $newest"

echo "-- Recent runs (run_log) --"
tail -5 "$REPO/logs/run_log.md" 2>/dev/null | sed 's/^/   /'

echo "-- Needs human (open alerts) --"
python3 -c "
import json
d=json.load(open('$REPO/comms/state.json'))
items=[f'   [{k}] {i}' for k,v in d.get('agents',{}).items() for i in (v.get('needs_human') or [])]
print('\n'.join(items) if items else '   none')
" 2>/dev/null
echo "================================================================================"

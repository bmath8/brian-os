#!/usr/bin/env bash
# Sync tracked runtime Python scripts -> the live ~/.hermes/scripts that cron runs.
# Brian runs this himself AFTER reviewing the branch (deploy = Yellow per GUARDRAILS).
# Idempotent. Strips CRLF (files are authored on Windows). Backs up the old copies.
set -euo pipefail

SRC="/mnt/c/Brian/02_Projects/brian-os-fleet/runtime"
DST="$HOME/.hermes/scripts"
STAMP=$(date +%Y%m%d-%H%M%S)
BAK="$HOME/.hermes/scripts_backup_$STAMP"

mkdir -p "$DST"
cp -r "$DST" "$BAK" 2>/dev/null || true
echo "Backed up current scripts -> $BAK"

n=0
for f in "$SRC"/*.py; do
  base=$(basename "$f")
  sed 's/\r$//' "$f" > "$DST/$base"
  n=$((n+1))
done
echo "Deployed $n .py scripts to $DST:"
ls -1 "$DST"/*.py

echo
echo "fleet_common.py present? -> $([ -f "$DST/fleet_common.py" ] && echo yes || echo NO)"
echo "Cron SCHEDULES unchanged, so NO gateway restart is required."
echo "Smoke test one agent now:  python3 $DST/daily_brief.py | head -5"
echo "Rollback:  rm -rf $DST && mv $BAK $DST"

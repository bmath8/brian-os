#!/usr/bin/env bash
# Nightly additive mirror of Harmony -> C:\Brian\Harmony_backup (off-OneDrive).
# Additive only (cp -u): updates/adds, never deletes — honors the "never delete" rule.
SRC=/mnt/c/Users/mathe/OneDrive/Desktop/Harmony
DST=/mnt/c/Brian/Harmony_backup
mkdir -p "$DST"
cp -ru "$SRC/." "$DST/" 2>/dev/null
n=$(find "$DST" -type f 2>/dev/null | wc -l)
echo "Harmony backup refreshed $(date '+%Y-%m-%d %H:%M') — $n files"

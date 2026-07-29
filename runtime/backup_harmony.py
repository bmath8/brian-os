#!/usr/bin/env python3
"""Harmony backup - additive mirror of the Harmony folder to an off-OneDrive location
(insurance against the OneDrive wipes). NEVER deletes. Cross-platform: robocopy on
native Windows, cp -ru on Linux/WSL. Replaces the old backup_harmony.sh so the job
runs on native Windows too."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc


def main():
    src, dst = fc.HARMONY, fc.HARMONY_BACKUP
    if not os.path.isdir(src):
        print(f"Harmony source not found: {src}")
        fc.log_run("harmony_backup", "alert", "source missing")
        return
    os.makedirs(dst, exist_ok=True)
    if fc.WINDOWS:
        # /E all subdirs, /XO skip older (additive), no purge; quiet flags.
        subprocess.run(["robocopy", src, dst, "/E", "/XO", "/R:1", "/W:1",
                        "/NFL", "/NDL", "/NP", "/NJH", "/NJS"], capture_output=True)
    else:
        subprocess.run(f"cp -ru '{src}/.' '{dst}/'", shell=True, capture_output=True)
    n = sum(len(f) for _, _, f in os.walk(dst))
    # Freshness stamp: the watchdog used to judge staleness by the NEWEST FILE MTIME
    # in the mirror -- but robocopy preserves source timestamps, so if Brian simply
    # hadn't edited Harmony for 3+ days the watchdog cried "backup stale" even though
    # the mirror ran fine every night (false alert every 4h). The stamp records when
    # the mirror itself last ran; the watchdog checks it first.
    fc.atomic_write(os.path.join(dst, ".last_backup"), fc.now())
    print(f"Harmony backup: {n} files mirrored to {dst}")
    fc.log_run("harmony_backup", "ok", f"{n} files")


if __name__ == "__main__":
    main()

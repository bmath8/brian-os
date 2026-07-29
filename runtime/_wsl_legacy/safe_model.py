#!/usr/bin/env python3
"""Resource-aware model gate. Agents call this to pick a model that WON'T thrash.
Reads comms/resource_status.json (RAM/commit pressure) and returns a safe model.

Usage:  MODEL=$(python3 safe_model.py [desired])
  - desired omitted -> best fit for current pressure
  - desired given (e.g. qwen3:14b) -> downgraded to qwen3:8b if memory is tight
"""
import json, sys, os, time, subprocess

COMMS = "/mnt/c/Brian/02_Projects/brian-os-fleet/comms"
PROBE = r"C:\Brian\02_Projects\brian-os-fleet\runtime\resource_probe.ps1"
SMALL, BIG = "qwen3:8b", "qwen3:14b"

def fresh():
    # Refresh the resource snapshot if it's missing or older than 5 min.
    try:
        if time.time() - os.path.getmtime(f"{COMMS}/resource_status.json") < 300:
            return
    except Exception:
        pass
    try:
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PROBE],
                       timeout=25, capture_output=True)
    except Exception:
        pass

def pressured():
    fresh()
    try:
        r = json.load(open(f"{COMMS}/resource_status.json"))
        # Commit (pagefile) pressure is the real signal on a 16GB box, BUT
        # percentages alone miss the edge case where commit sits just under the
        # threshold yet only ~2GB RAM is actually free — loading 14B (~9GB, and
        # ~14-19GB at 64K ctx) would still thrash. Gate on BOTH: percentage
        # pressure AND an absolute free-RAM floor for the big model.
        if r.get("commit_pct", 0) >= 88 or r.get("ram_pct", 0) >= 88:
            return True
        if r.get("ram_free_gb", 99) < 12:   # not enough headroom to run 14B safely
            return True
        return False
    except Exception:
        return True  # unknown -> play safe, use the small model

desired = sys.argv[1] if len(sys.argv) > 1 else BIG
print(SMALL if pressured() else desired)

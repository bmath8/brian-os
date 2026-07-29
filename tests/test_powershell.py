#!/usr/bin/env python3
"""CI guards for the PowerShell layer + status-check hygiene.

Two silent self-heal deaths have shipped via patterns no test caught:
  1) 06-20: `"$st" -match 'running'` was true for "NOT running" (keepalive never healed)
  2) 07-10: `function AgeMin($pid)` bound the READ-ONLY automatic $pid -> the guardian
     aborted every tick for days (160 orphans, pagefile ate the disk).
These tests make both bug classes impossible to ship again.
"""
import os, re, glob, subprocess, sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PS_FILES = glob.glob(os.path.join(ROOT, "runtime", "*.ps1")) + \
           glob.glob(os.path.join(ROOT, "shared", "*.ps1"))

# Read-only / auto-populated PowerShell variables that must never be assigned,
# used as a parameter, or used as a loop variable.
AUTO_VARS = ("pid", "error", "input", "host", "args", "profile", "home")

_ASSIGN = [re.compile(p % v, re.I) for v in AUTO_VARS for p in (
    r"function\s+\w+\s*\(\s*\$%s\b",       # function F($pid)
    r"param\s*\([^)]*\$%s\b",               # param($pid)
    r"foreach\s*\(\s*\$%s\s+in\b",          # foreach ($pid in ...)
    r"^\s*\$%s\s*=",                          # $pid = ...
)]


def _strip_comments(text):
    text = re.sub(r"<#.*?#>", "", text, flags=re.S)
    return "\n".join(ln.split("#", 1)[0] if "#" in ln and not ln.strip().startswith('"')
                     else ln for ln in text.splitlines())


def test_no_automatic_variable_shadowing():
    assert PS_FILES, "no .ps1 files found - path wrong?"
    bad = []
    for f in PS_FILES:
        body = _strip_comments(open(f, encoding="utf-8", errors="ignore").read())
        for ln_no, ln in enumerate(body.splitlines(), 1):
            for pat in _ASSIGN:
                if pat.search(ln):
                    bad.append(f"{os.path.basename(f)}:{ln_no}: {ln.strip()[:90]}")
    assert not bad, ("PowerShell automatic variable shadowed (read-only; aborts the "
                     "script at runtime):\n" + "\n".join(bad))


def test_no_bare_running_substring_checks():
    """Any 'running' status string-match must exclude the negative ('not running')."""
    offenders = []
    for f in glob.glob(os.path.join(ROOT, "runtime", "*.py")) + \
             glob.glob(os.path.join(ROOT, "shared", "*.py")):
        lines = open(f, encoding="utf-8", errors="ignore").read().splitlines()
        for i, ln in enumerate(lines):
            if re.search(r"""['"]running['"]\s+in\s""", ln) and "not running" not in ln:
                ctx = " ".join(lines[max(0, i - 2):i + 3])
                if "not running" not in ctx:
                    offenders.append(f"{os.path.basename(f)}:{i+1}")
    for f in PS_FILES:
        body = _strip_comments(open(f, encoding="utf-8", errors="ignore").read())
        for i, ln in enumerate(body.splitlines(), 1):
            if re.search(r"-match\s+'running'", ln, re.I):
                offenders.append(f"{os.path.basename(f)}:{i}")
    assert not offenders, "bare 'running' substring status check (matches 'NOT running' too): " + ", ".join(offenders)


@pytest.mark.skipif(os.name != "nt", reason="windows only")
def test_process_guardian_runs_clean():
    """Execute the guardian for real (-Quiet). It must exit 0 with an EMPTY stderr -
    the $pid bug produced a terminating error on stderr while exit codes lied."""
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(ROOT, "runtime", "process_guardian.ps1"), "-Quiet"],
        capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"guardian exit {r.returncode}: {r.stderr[:300]}"
    assert not (r.stderr or "").strip(), f"guardian wrote to stderr: {r.stderr[:300]}"

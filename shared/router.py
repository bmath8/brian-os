#!/usr/bin/env python3
"""
Fleet Router v2 -- best-tool-per-task, free-first, redact-first.

Policy (decisions 2026-06-25):
  * LOCAL FIRST, ALWAYS. qwen3 (via fleet_common.ollama_generate) handles cron +
    drafts at $0. Escalate ONLY on local failure, low-confidence self-check, or a
    task explicitly flagged high-stakes / user_facing_final.
  * SUBS, NOT KEYS (Q1). Escalation does NOT call paid APIs. It shells out to the
    CLIs Brian already pays a flat rate for:
        - Claude Code CLI  -> Opus 4.8   (prose / voice-matched drafts)
        - Codex CLI        -> GPT-5.5     (structure / ATS / code / math)
    Configure the exact commands in .env (CLAUDE_CLI_CMD / CODEX_CLI_CMD); if a CLI
    isn't found the router degrades gracefully and returns the local draft plus a
    note telling Brian to run the escalation by hand.
  * REDACT FIRST (Q2). Before ANY text leaves the box for a cloud CLI, PII is
    stripped to placeholders (fleet_common.redact_pii); the returned draft is
    un-redacted LOCALLY (restore_pii) so Brian sees real details but the cloud never did.
  * ENSEMBLE on the few things that matter: high-stakes tasks can ask BOTH Opus and
    GPT, returning both drafts for Brian to pick/merge -- effectively free on his subs.

This module RETURNS drafts to the caller (for the approval queue / blackboard). It
never sends to third parties and never auto-applies a draft -- the draft-only
guardrail is preserved.

CLI usage:
    python router.py --task application --stakes high "Draft a cover letter for ..."
    python router.py --task summarize "long text..."
    echo "..." | python router.py --task draft --ensemble
Returns JSON: {tier, model, escalated, ensemble, output, alternates, redacted, ms, notes}
"""
import argparse, json, os, shutil, subprocess, sys, time, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = os.path.join(os.path.dirname(HERE), "runtime")
sys.path.insert(0, RUNTIME)
import fleet_common as fc  # noqa: E402

REG_PATH = os.path.join(HERE, "models.json")
REG = json.load(open(REG_PATH, encoding="utf-8")) if os.path.exists(REG_PATH) else {}

# task -> default complexity (override with --complexity / --stakes high)
TASK_DEFAULTS = {
    "classify": "simple", "parse": "simple", "extract": "simple", "tag": "simple",
    "route": "trivial", "short_summary": "simple", "quick_draft": "simple",
    "summarize": "moderate", "analysis": "moderate", "draft": "moderate",
    "plan": "complex", "reason": "complex", "code": "complex",
    "final_email": "user_facing_final", "application": "hard", "cover_letter": "hard",
    "outreach": "hard", "interview_prep": "hard",
}
HIGH_STAKES = {"hard", "user_facing_final"}
UNCERTAIN = ("i'm not sure", "i am not sure", "cannot determine", "as an ai model",
             "i don't have enough", "insufficient information", "i cannot")

# Which CLI is the right primary for a given task (prose -> Opus, code/math -> GPT).
CODE_OR_MATH = {"code", "reason", "plan", "analysis"}


def _complexity(task, override):
    return override or TASK_DEFAULTS.get(task or "", "moderate")


def _low_confidence(text):
    t = (text or "").lower()
    return (len(text.strip()) < 8) or any(u in t for u in UNCERTAIN)


def _cli_for(name):
    """Resolve a CLI command from env, falling back to a bare name on PATH.
    Returns a list (argv prefix) or None if not found."""
    env = (os.environ.get(name) or "").strip()
    if env:
        # The whole value may be ONE path containing spaces (C:\Program Files\...).
        # Try it verbatim before splitting on whitespace (fixed 2026-07-06).
        exe = shutil.which(env) or (env if os.path.exists(env) else None)
        if exe:
            return [exe]
        parts = env.split()
        exe = shutil.which(parts[0]) or (parts[0] if os.path.exists(parts[0]) else None)
        return ([exe] + parts[1:]) if exe else None
    default = {"CLAUDE_CLI_CMD": "claude", "CODEX_CLI_CMD": "codex"}.get(name)
    found = shutil.which(default) if default else None
    return [found] if found else None


def _run_cli(argv, prompt, timeout=240):
    """Pipe `prompt` to a CLI in non-interactive/print mode, return stdout text.
    Most coding CLIs accept the prompt on stdin and a print/non-interactive flag;
    we pass it on stdin and let env-configured flags (in CLAUDE_CLI_CMD) do the rest."""
    try:
        p = subprocess.run(argv, input=prompt, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "").strip()
        return out or None
    except Exception:
        return None


def _escalate(prompt, prefer_gpt):
    """Try the preferred cloud CLI (Opus or GPT) on REDACTED text, restore PII locally.
    Returns (model_label, output_or_None, note)."""
    mapping = {}
    safe = fc.redact_pii(fc.redact_secrets(prompt), mapping)
    order = [("GPT-5.5 (Codex)", "CODEX_CLI_CMD"), ("Opus 4.8 (Claude Code)", "CLAUDE_CLI_CMD")]
    if not prefer_gpt:
        order.reverse()
    for label, env in order:
        argv = _cli_for(env)
        if not argv:
            continue
        out = _run_cli(argv, safe)
        if out:
            return label, fc.restore_pii(out, mapping), f"escalated via {label} (redact-first, {len(mapping)} PII masked)"
    return None, None, ("no escalation CLI found (set CLAUDE_CLI_CMD / CODEX_CLI_CMD in .env) "
                        "-- returning local draft; run the cloud pass manually for final")


def route(prompt, task=None, complexity=None, stakes=None, ensemble=False, reflect=False):
    cx = _complexity(task, complexity)
    if stakes == "high":
        cx = "hard"
    high = cx in HIGH_STAKES
    notes = [f"task={task or '-'} complexity={cx}"]
    t0 = time.time()

    # 1) LOCAL FIRST -- always, even for high-stakes (free-first).
    local = fc.ollama_generate(prompt, num_ctx=8192, temperature=0.4,
                               timeout=120, retries=1, fallback=None) if _ollama_ok() else None
    if local is None:
        notes.append("local generate failed/unavailable")
    elif reflect:
        # Self-review pass on the local draft before it goes anywhere (#0.7).
        local = fc.reflect(local, task=task or "draft")
        notes.append("local draft self-reviewed (reflect)")
    ms = int((time.time() - t0) * 1000)

    # 2) Decide whether to escalate. Policy (docstring): high-stakes, LOCAL FAILURE,
    #    or a low-confidence local draft. (local is None previously did NOT escalate,
    #    contradicting the stated policy - fixed 2026-07-06.)
    escalate = high or (local is None) or _low_confidence(local)
    if not escalate:
        _log(task, "local", False, ms, True, tools=[{"name": "ollama", "ok": True}])
        return {"tier": 1, "model": fc.DEFAULT_MODEL, "escalated": False, "ensemble": False,
                "output": local, "alternates": [], "redacted": False, "ms": ms, "notes": notes}

    prefer_gpt = (task in CODE_OR_MATH) or fc.is_code_task(prompt)
    primary_label, primary_out, note = _escalate(prompt, prefer_gpt)
    notes.append(note)

    alternates = []
    if ensemble and primary_out is not None:
        # Ask the OTHER CLI too, so Brian can pick/merge. Free on his subs.
        other_label, other_out, n2 = _escalate(prompt, not prefer_gpt)
        notes.append(n2)
        if other_out is not None and other_label != primary_label:
            alternates.append({"model": other_label, "output": other_out})

    ms = int((time.time() - t0) * 1000)
    if primary_out is None:
        # CLIs unavailable -> hand back the local draft + the manual-escalation note.
        _log(task, "local->manual", True, ms, local is not None,
             tools=[{"name": "ollama", "ok": local is not None}, {"name": "cli", "ok": False}])
        return {"tier": 1, "model": fc.DEFAULT_MODEL, "escalated": False, "ensemble": False,
                "output": local, "alternates": [], "redacted": False, "ms": ms,
                "notes": notes, "action": "ESCALATE_MANUAL"}

    _log(task, primary_label, True, ms, True,
         tools=[{"name": "ollama", "ok": local is not None},
                {"name": "redact_pii", "ok": True},
                {"name": primary_label, "ok": True}])
    return {"tier": 3, "model": primary_label, "escalated": True, "ensemble": bool(alternates),
            "output": primary_out, "alternates": alternates, "redacted": True,
            "local_draft": local, "ms": ms, "notes": notes}


def _ollama_ok():
    try:
        import urllib.request
        urllib.request.urlopen(f"{fc.ollama_url()}/api/tags", timeout=3)
        return True
    except Exception:
        return False


def _log(task, model, escalated, ms, ok, tools=None):
    tier = 3 if escalated else 1
    status = "ok" if ok else "fail"
    try:
        fc.log_run("router", status=status,
                   detail=f"{task or '-'} -> {model}{' (cloud)' if escalated else ''}",
                   tier=tier, ms=ms)
    except Exception:
        pass
    # Machine-readable trajectory record for evals (#0.5).
    try:
        fc.log_trajectory("router", task=task, model=model, tier=tier,
                          escalated=escalated, status=status,
                          tools=tools or [], ms=ms)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", default=None)
    ap.add_argument("--task", default=None)
    ap.add_argument("--complexity", default=None,
                    help="trivial|simple|moderate|complex|hard|user_facing_final")
    ap.add_argument("--stakes", default=None, choices=[None, "high"],
                    help="force high-stakes escalation")
    ap.add_argument("--ensemble", action="store_true",
                    help="ask BOTH Opus and GPT, return both for pick/merge")
    ap.add_argument("--reflect", action="store_true",
                    help="self-review the local draft before returning")
    a = ap.parse_args()
    prompt = a.prompt or (sys.stdin.read() if not sys.stdin.isatty() else None)
    if not prompt:
        print("No prompt provided.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(route(prompt, a.task, a.complexity, a.stakes, a.ensemble, a.reflect),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

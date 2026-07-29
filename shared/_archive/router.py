#!/usr/bin/env python3
"""
Fleet Router — open/free models FIRST, routed by capability.

Policy (see models.json): always try a LOCAL Ollama model first, chosen by task
complexity. Escalate to cloud ONLY on local failure, low-confidence, or when the
task is explicitly flagged user_facing_final / high_stakes.

Usage:
    python router.py --task summarize --complexity simple "text to summarize"
    python router.py --complexity moderate "Draft a 3-sentence intro about X"
    echo "long text..." | python router.py --task long_summary

Returns JSON: {model, tier, escalated, output, ms, notes}
Logs one line to ../logs/run_log.md.
"""
import argparse, json, os, sys, time, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REG = json.load(open(os.path.join(HERE, "models.json"), encoding="utf-8"))
LOG = os.path.join(HERE, "..", "logs", "run_log.md")
def _ollama_url():
    # Honor an explicit override first.
    env = os.environ.get("OLLAMA_URL")
    if env:
        return env
    # In WSL, localhost is the VM — Ollama runs on the Windows host. Derive the
    # default-gateway IP (same trick the cron agents use). On a real host, use localhost.
    if os.path.exists("/mnt/c"):
        try:
            import subprocess
            ip = subprocess.check_output("ip route | awk '/default/{print $3}'", shell=True, text=True).strip()
            if ip:
                return f"http://{ip}:11434"
        except Exception:
            pass
    return "http://localhost:11434"

OLLAMA = _ollama_url()

# task_type -> default complexity (override with --complexity)
TASK_DEFAULTS = {
    "classify": "simple", "parse": "simple", "extract": "simple", "tag": "simple",
    "route": "trivial", "short_summary": "simple", "quick_draft": "simple",
    "summarize": "moderate", "long_summary": "moderate", "analysis": "moderate",
    "draft": "moderate", "plan": "complex", "reason": "complex",
    "code": "complex", "final_email": "user_facing_final", "application": "hard",
}

UNCERTAIN = ("i'm not sure", "i am not sure", "cannot determine", "as an ai",
             "i don't have enough", "insufficient information")


def pick(task_type, complexity):
    if not complexity:
        complexity = TASK_DEFAULTS.get(task_type, "moderate")
    target = REG["complexity_to_model"].get(complexity, "qwen3:8b")
    return complexity, target


def ollama_list():
    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=3) as r:
            return [m["name"] for m in json.load(r).get("models", [])]
    except Exception:
        return []


def run_local(model, prompt):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r).get("response", "").strip()


def low_confidence(text):
    t = (text or "").lower()
    return (len(text.strip()) < 8) or any(u in t for u in UNCERTAIN)


def log(model, tier, escalated, ms, ok):
    line = (f"{datetime.datetime.now().isoformat(timespec='seconds')} | router | "
            f"tier{tier}{'->cloud' if escalated else ''} | {'ok' if ok else 'fail'} | "
            f"{model} {ms}ms\n")
    try:
        open(LOG, "a", encoding="utf-8").write(line)
    except Exception:
        pass


def route(prompt, task_type=None, complexity=None):
    complexity, target = pick(task_type, complexity)
    available = ollama_list()
    notes = []

    # If the chosen target is an escalation flag, try the strongest LOCAL model
    # first anyway (free-first policy) before recommending cloud.
    if str(target).startswith("ESCALATE"):
        # Prefer the strongest installed local model, in capability order.
        ranked = ["deepseek-r1:14b", "qwen3:14b", "qwen3:8b"]
        local_try = next((m for m in ranked if m in available), (available[0] if available else None))
        notes.append(f"complexity={complexity} suggests cloud; trying local {local_try} first per free-first policy")
        target = local_try

    if not target or target not in available:
        # desired local model missing -> fall back to any available local model
        fallback = available[0] if available else None
        if fallback:
            notes.append(f"requested model unavailable; using local {fallback}")
            target = fallback
        else:
            notes.append("NO local Ollama models reachable -> would escalate to cloud (add keys in shared/.env)")
            log("none", 1, True, 0, False)
            return {"model": None, "tier": 1, "escalated": True, "output": None,
                    "ms": 0, "notes": notes, "action": "ESCALATE_CLOUD"}

    t0 = time.time()
    try:
        out = run_local(target, prompt)
        ms = int((time.time() - t0) * 1000)
    except Exception as e:
        notes.append(f"local error: {e} -> recommend cloud escalation")
        log(target, 1, True, int((time.time()-t0)*1000), False)
        return {"model": target, "tier": 1, "escalated": True, "output": None,
                "ms": int((time.time()-t0)*1000), "notes": notes, "action": "ESCALATE_CLOUD"}

    escalate = low_confidence(out) or complexity in ("hard", "user_facing_final")
    if escalate:
        notes.append("local result low-confidence or high-stakes -> review/escalate to cloud for final")
    log(target, 1, escalate, ms, True)
    return {"model": target, "tier": 1, "escalated": escalate, "output": out,
            "ms": ms, "notes": notes,
            "action": "USE_LOCAL" if not escalate else "USE_LOCAL_OR_ESCALATE"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", default=None)
    ap.add_argument("--task", default=None)
    ap.add_argument("--complexity", default=None,
                    help="trivial|simple|moderate|complex|hard|user_facing_final")
    a = ap.parse_args()
    prompt = a.prompt or (sys.stdin.read() if not sys.stdin.isatty() else None)
    if not prompt:
        print("No prompt provided.", file=sys.stderr); sys.exit(1)
    print(json.dumps(route(prompt, a.task, a.complexity), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

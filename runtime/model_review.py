#!/usr/bin/env python3
"""Model review - keeps the fleet's models current (Brian's "always update to the best").

Spot-checks every INSTALLED local Ollama model on a tiny fixed prompt (latency + ok/fail),
writes comms/model_review.md, and prints the refresh checklist. SAFE on a memory-constrained
box: tiny prompts, keep_alive=0 (unload after), per-model timeout so a too-heavy model just
times out and is flagged.

Run by hand:   python3 model_review.py            (all installed models)
               python3 model_review.py --quick    (only models <=9GB-ish)
Cadence: monthly, off-peak.
"""
import os, sys, json, urllib.request, datetime, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

QUICK = "--quick" in sys.argv
PROMPT = "In one sentence, what is the capital of France and why is it significant?"
PER_MODEL_TIMEOUT = 60


def installed():
    try:
        with urllib.request.urlopen(f"{fc.ollama_url()}/api/tags", timeout=5) as r:
            return [(m["name"], m.get("size", 0)) for m in json.load(r).get("models", [])]
    except Exception:
        return []


def probe(model):
    body = json.dumps({"model": model, "prompt": PROMPT, "stream": False, "think": False,
                       "keep_alive": 0, "options": {"num_ctx": 2048, "num_predict": 60}}).encode()
    req = urllib.request.Request(f"{fc.ollama_url()}/api/generate", body, {"Content-Type": "application/json"})
    t0 = time.time()
    try:
        out = json.load(urllib.request.urlopen(req, timeout=PER_MODEL_TIMEOUT)).get("response", "")
        return round(time.time() - t0, 1), len(out.strip()), "ok"
    except Exception as e:
        return round(time.time() - t0, 1), 0, f"FAIL/too-heavy ({type(e).__name__})"


def main():
    models = installed()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    for name, size in sorted(models):
        gb = size / 1e9
        if QUICK and gb > 9:
            rows.append((name, f"{gb:.1f}", "-", "-", "skipped (--quick, too big)"))
            continue
        secs, chars, status = probe(name)
        rows.append((name, f"{gb:.1f}", str(secs), str(chars), status))

    md = [f"# Model Review - {stamp}", "",
          "Installed local models, quick spot-check (tiny prompt, keep_alive=0).", "",
          "| Model | Size GB | Latency s | Out chars | Status |",
          "|---|---|---|---|---|"]
    md += [f"| {n} | {g} | {s} | {c} | {st} |" for (n, g, s, c, st) in rows]
    md += ["",
           "## Refresh checklist (run monthly)",
           "1. Web-search 'best local LLM <current month> 12GB VRAM' + check Ollama library for newer small models.",
           "2. Compare any candidate against the current default (qwen3:8b) on the fleet's real tasks via tests/eval_models.py.",
           "3. Keep the winner as default; update shared/models.json + ROUTING.md; log it here + run_log.md.",
           "4. Refresh the cloud escalation ladder (cheapest current Tier-A) in models.json cloud_fallback.",
           "5. Re-check the RAM-upgrade trigger: once 64GB lands, set FLEET_MODEL=qwen3:14b (one place).",
           "",
           "See MODELS_AND_TOOLS_REVIEW_2026-06-17.md for the last full review."]
    # Monthly security audit (2026-07-11, backlog #20): piggyback on this monthly cron.
    # `hermes security` is guarded - unsupported/failed just reports "skipped".
    try:
        import subprocess as _sp
        _hx = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes",
                           "hermes-agent", "venv", "Scripts", "hermes.exe")
        _r = _sp.run([_hx, "security"], timeout=180, capture_output=True,
                     text=True, encoding="utf-8", errors="replace")
        _sec = ((_r.stdout or "") + (_r.stderr or "")).strip()
        _flags = [l.strip() for l in _sec.splitlines()
                  if any(k in l for k in ("✗", "✘", "FAIL", "WARN", "HIGH", "CRITICAL"))]
        md += ["", "## Monthly security audit (hermes security)",
               ("- " + "\n- ".join(f[:100] for f in _flags[:8])) if _flags
               else ("- clean" if _r.returncode == 0 else "- skipped (command unavailable)")]
    except Exception:
        md += ["", "## Monthly security audit", "- skipped (error running hermes security)"]

    fc.atomic_write(f"{fc.COMMS}/model_review.md", "\n".join(md) + "\n")
    _msg = "\n".join(md)
    fc.telegram_send(_msg, urgent=True)            # direct API (update-proof)
    print(fc.ascii_fold(_msg))
    fc.log_run("model_review", "ok", f"{len(rows)} models checked")


if __name__ == "__main__":
    main()

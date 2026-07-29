#!/usr/bin/env python3
"""End-to-end smoke tests for the agents. Each agent is run against a MOCK Ollama
and a temp Harmony/comms tree, asserting it writes its output file and leaves a
valid state.json. No network, no PowerShell, no real model. Stdlib only.

(The watchdog is intentionally excluded: it self-heals via real PowerShell/bash
subprocesses, which must not run inside a test.)
"""
import os, sys, json, glob, tempfile, threading, importlib, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

_TMP = tempfile.mkdtemp(prefix="fleet_smoke_")
os.environ["FLEET_ROOT"] = _TMP
os.environ["FLEET_COMMS"] = os.path.join(_TMP, "comms")
os.environ["FLEET_LOGS"] = os.path.join(_TMP, "logs")
os.environ["HARMONY_DIR"] = os.path.join(_TMP, "harmony")
os.environ["HARMONY_BACKUP_DIR"] = os.path.join(_TMP, "harmony_bk")
RUNTIME = os.path.join(os.path.dirname(__file__), "..", "runtime")
sys.path.insert(0, RUNTIME)
import fleet_common as fc  # noqa: E402

CANNED = ("Top priority: send 5 tailored job applications.\n"
          "Top 3: 1) Apps 2) Portfolio 3) Fitness.\nYou're making real progress.")


class _Mock:
    def __enter__(self):
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):   # /api/tags for model_review + watchdog
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(
                    {"models": [{"name": "qwen3:8b", "size": 5_000_000_000}]}).encode())

            def do_POST(self):  # /api/generate
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n) or b"{}")
                # structured-output requests (synthesis) get valid JSON back
                if payload.get("format"):
                    resp = json.dumps({"one_thing": "Send 5 tailored applications",
                                       "connections": ["Runway is tight vs. low application pace"]})
                else:
                    resp = CANNED
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"response": resp}).encode())

        self.server = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        os.environ["OLLAMA_URL"] = f"http://127.0.0.1:{self.server.server_address[1]}"
        return self

    def __exit__(self, *a):
        self.server.shutdown()
        os.environ.pop("OLLAMA_URL", None)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


def setUpModule():
    H = fc.HARMONY
    _write(os.path.join(H, "Dashboard.md"), "# Dashboard\nJob hunt is priority one.\n")
    _write(os.path.join(H, "03_Career", "Job_Tracker.md"),
           "| Metric | Target | Actual |\n|---|---:|---:|\n"
           "| Applications sent | 25 | 4 |\n| Networking touches | 5 | 2 |\n"
           "| Interviews scheduled | >=1 | 0 |\n\n- Primary: Full-Stack Developer · AI Engineer\n")
    _write(os.path.join(H, "05_Finance", "Finance_Tracker_and_Credit_Plan.md"), "# Finance\nCash: blank\n")
    _write(os.path.join(H, "05_Finance", "Credit_Rebuild_Action_Plan.md"), "# Credit\nStep 1: blank\n")
    _write(os.path.join(H, "04_Health", "Health_Baseline_and_Tracker.md"), "# Health\nWeekly log: /3 /7\n")
    _write(os.path.join(fc.ROOT, "TIPS_AND_OPTIMIZATIONS.md"), "# Tips\nAlways verify the 0.0.0.0 bind.\n")
    os.makedirs(fc.COMMS, exist_ok=True)


class AgentSmokeTests(unittest.TestCase):
    def _run(self, modname, patch=None):
        mod = importlib.import_module(modname)
        importlib.reload(mod)
        if patch:
            patch(mod)
        with _Mock():
            mod.main()
        if os.path.exists(fc.STATE):
            json.load(open(fc.STATE))  # must stay valid JSON

    def test_daily_brief(self):
        self._run("daily_brief")
        brief = fc.read(f"{fc.COMMS}/daily_brief.md")
        self.assertTrue(os.path.exists(f"{fc.COMMS}/daily_brief.md"))
        self.assertIn("Job hunt this week", brief)
        self.assertIn("Today's ONE thing", brief)   # synthesis pass ran
        self.assertTrue(glob.glob(f"{fc.COMMS}/briefs/*.md"))

    def test_finance(self):
        self._run("finance_agent")
        self.assertTrue(os.path.exists(f"{fc.COMMS}/finance.md"))

    def test_health(self):
        self._run("health_agent")
        self.assertTrue(os.path.exists(f"{fc.COMMS}/health.md"))

    def test_learning(self):
        def patch(mod):
            mod._generate_questions = lambda: ["What binds Ollama to 0.0.0.0?",
                                               "What fixes the state.json race?",
                                               "Why a separate critic model?"]
        self._run("learning_agent", patch)
        recall = fc.read(f"{fc.COMMS}/recall.md")
        self.assertTrue(os.path.exists(f"{fc.COMMS}/recall.md"))
        self.assertIn("[id ", recall)   # SRS cards surfaced with ids

    def test_feedback(self):
        _write(f"{fc.COMMS}/review/approved/a.md", "## Draft\nGood draft.\n---\n")
        _write(f"{fc.COMMS}/review/rejected/b.md", "## Draft\nBad draft.\n---\n")
        fb = importlib.import_module("feedback")
        importlib.reload(fb)
        with _Mock():
            fb.main()
            fb.main()   # second run must NOT double-count
        self.assertTrue(os.path.exists(f"{fc.COMMS}/feedback.md"))
        lines = [l for l in fc.read(f"{fc.COMMS}/.feedback/outcomes.jsonl").splitlines() if l.strip()]
        self.assertEqual(len(lines), 2)   # idempotent

    def test_weekly_review(self):
        self._run("weekly_review")
        self.assertTrue(glob.glob(os.path.join(fc.HARMONY, "02_Weekly_Reviews", "*.md")))

    def test_scout(self):
        def patch(mod):
            mod.ddg_search = lambda q, limit=5: [{"title": "Remote Dev", "url": "https://example.com/job"}]
        self._run("scout_agent", patch)
        self.assertTrue(os.path.exists(f"{fc.COMMS}/scout.md"))
        self.assertIn("example.com", fc.read(f"{fc.COMMS}/scout.md"))

    def test_model_review(self):
        self._run("model_review")
        self.assertTrue(os.path.exists(f"{fc.COMMS}/model_review.md"))

    def test_overnight_worker(self):
        _write(f"{fc.COMMS}/queue/task1.md", "# Write a haiku about shipping code\nDo it.")
        self._run("overnight_worker")
        self.assertTrue(glob.glob(f"{fc.COMMS}/review/*.md"))
        self.assertTrue(glob.glob(f"{fc.COMMS}/queue/done/*.md"))


class OpsToolTests(unittest.TestCase):
    def test_log_analyzer(self):
        import datetime
        fc.atomic_write(fc.RUN_LOG,
                        f"{datetime.datetime.now().isoformat(timespec='seconds')} | chief_of_staff | tier1 | ok | 2 needs | 1200ms\n"
                        f"{datetime.datetime.now().isoformat(timespec='seconds')} | health | tier1 | fail | err\n")
        la = importlib.import_module("log_analyzer")
        importlib.reload(la)
        stats = la.analyze(7)
        self.assertIn("chief_of_staff", stats)
        text, flags = la.render(stats, 7)
        self.assertTrue(any("health" in f for f in flags))  # the failure is flagged
        la.main()
        self.assertTrue(os.path.exists(f"{fc.COMMS}/fleet_health.md"))

    def test_build_dashboard(self):
        fc.state_update("finance", {"last_run": "2026-06-18", "status": "ok",
                                    "summary": "runway blank", "needs_human": ["fill expenses"]})
        bd = importlib.import_module("build_dashboard")
        importlib.reload(bd)
        bd.main()
        out = fc.read(f"{fc.COMMS}/dashboard.html")
        self.assertIn("Brian OS Fleet", out)
        self.assertIn("finance", out)


class AgeNeedsTests(unittest.TestCase):
    def test_chronic_item_hidden_midweek(self):
        import datetime
        try:
            os.remove(os.path.join(fc.COMMS, ".needs_age.json"))
        except OSError:
            pass
        tue = datetime.date(2026, 6, 16)   # a Tuesday
        item = ["[finance] fill tracker"]
        for _ in range(2):
            fc.age_needs(item, today=datetime.date(2026, 6, 14))  # seed prior days
        fc.age_needs(item, today=datetime.date(2026, 6, 15))
        # now 3 distinct days seen -> chronic -> hidden on a non-Monday
        self.assertEqual(fc.age_needs(item, today=tue), [])
        # but shown on Monday
        self.assertEqual(fc.age_needs(item, today=datetime.date(2026, 6, 22)), item)


if __name__ == "__main__":
    unittest.main()

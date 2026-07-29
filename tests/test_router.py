#!/usr/bin/env python3
"""Tests for the redact-first multi-model router (shared/router.py) and the PII
gate in fleet_common. Stdlib only. Run: python3 -m unittest discover -s tests

Codifies the two 2026-06-25 decisions so they can't silently regress:
  * Q2 redact-first: PII never leaves the box on an escalation path.
  * Q1 subs-not-keys: with no escalation CLI configured, the router degrades to a
    local draft + manual-escalation note instead of failing or leaking.
"""
import os, sys, tempfile, unittest

_TMP = tempfile.mkdtemp(prefix="router_test_")
os.environ["FLEET_ROOT"] = _TMP
os.environ["FLEET_COMMS"] = os.path.join(_TMP, "comms")
os.environ["FLEET_LOGS"] = os.path.join(_TMP, "logs")
os.environ["BRIAN_PII"] = "Brian Mathew,Brian"          # configured personal terms
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runtime"))
sys.path.insert(0, os.path.join(ROOT, "shared"))
import fleet_common as fc  # noqa: E402
import router  # noqa: E402


class TestPIIRedaction(unittest.TestCase):
    def test_masks_email_phone_name(self):
        m = {}
        red = fc.redact_pii("Brian Mathew, mathew.brian@gmail.com, (555) 123-4567", m)
        self.assertNotIn("mathew.brian@gmail.com", red)
        self.assertNotIn("555", red)
        self.assertNotIn("Brian Mathew", red)
        self.assertTrue(any(k.startswith("[EMAIL") for k in m))
        self.assertTrue(any(k.startswith("[PHONE") for k in m))
        self.assertTrue(any(k.startswith("[NAME") for k in m))

    def test_round_trip_restores(self):
        m = {}
        original = "Contact Brian at mathew.brian@gmail.com or 555-123-4567."
        red = fc.redact_pii(original, m)
        self.assertEqual(fc.restore_pii(red, m), original)

    def test_address_masked(self):
        m = {}
        red = fc.redact_pii("Ship to 1234 Maple Street today", m)
        self.assertNotIn("1234 Maple Street", red)

    def test_noop_safe(self):
        self.assertEqual(fc.redact_pii("", {}), "")
        self.assertEqual(fc.redact_pii(None), None)
        self.assertEqual(fc.restore_pii("x", {}), "x")


class TestEscalationDegradation(unittest.TestCase):
    def setUp(self):
        # Ensure no escalation CLI resolves, so we test the safe-degrade path.
        os.environ["CLAUDE_CLI_CMD"] = "/nonexistent/claude-xyz"
        os.environ["CODEX_CLI_CMD"] = "/nonexistent/codex-xyz"

    def test_escalate_no_cli_returns_note_not_crash(self):
        label, out, note = router._escalate("Draft for Brian at mathew.brian@gmail.com", prefer_gpt=True)
        self.assertIsNone(label)
        self.assertIsNone(out)
        self.assertIn("no escalation CLI", note)

    def test_escalate_redacts_before_any_cli(self):
        # Capture what _run_cli would have been handed; assert PII already masked.
        seen = {}
        orig = router._run_cli

        def spy(argv, prompt, timeout=240):
            seen["prompt"] = prompt
            return "DRAFT OK"
        router._run_cli = spy
        router._cli_for = lambda name: ["/bin/true"]    # pretend a CLI exists
        try:
            label, out, note = router._escalate(
                "Cover letter for Brian Mathew, mathew.brian@gmail.com", prefer_gpt=True)
        finally:
            router._run_cli = orig
        self.assertIn("prompt", seen)
        self.assertNotIn("mathew.brian@gmail.com", seen["prompt"])   # never leaves un-redacted
        self.assertNotIn("Brian Mathew", seen["prompt"])
        self.assertEqual(out, "DRAFT OK")


class TestTrajectoryLog(unittest.TestCase):
    def test_log_and_stats_round_trip(self):
        # Fresh log location for isolation.
        import importlib
        log = fc.TRAJECTORY_LOG
        if os.path.exists(log):
            os.remove(log)
        fc.log_trajectory("router", task="application", model="Opus 4.8 (Claude Code)",
                          tier=3, escalated=True, status="ok",
                          tools=[{"name": "ollama", "ok": True}], ms=1200)
        fc.log_trajectory("router", task="summarize", model="qwen3:8b",
                          tier=1, escalated=False, status="ok", ms=80)
        fc.log_trajectory("router", task="parse", model="qwen3:8b",
                          tier=1, escalated=False, status="fail", ms=50)
        self.assertTrue(os.path.exists(log))
        stats = fc.trajectory_stats()
        self.assertEqual(stats["n"], 3)
        self.assertEqual(stats["by_agent"]["router"]["runs"], 3)
        self.assertEqual(stats["by_agent"]["router"]["fails"], 1)
        self.assertEqual(stats["by_agent"]["router"]["escalated"], 1)

    def test_stats_tolerates_rotate_header(self):
        with open(fc.TRAJECTORY_LOG, "a", encoding="utf-8") as fh:
            fh.write("<!-- rotated 2026-06-26: kept last N lines -->\n")
        # Should not raise or count the non-JSON line.
        stats = fc.trajectory_stats()
        self.assertIsInstance(stats["n"], int)

    def test_log_trajectory_noop_safe(self):
        # Bad input shouldn't raise.
        try:
            fc.log_trajectory(None)
        except Exception as e:
            self.fail(f"log_trajectory raised: {e}")


class TestReflection(unittest.TestCase):
    def test_reflect_returns_improved(self):
        orig = fc.ollama_generate
        fc.ollama_generate = lambda *a, **k: "This is the improved, tighter draft text."
        try:
            out = fc.reflect("rough draft that is somewhat long and wordy", task="cover_letter")
        finally:
            fc.ollama_generate = orig
        self.assertEqual(out, "This is the improved, tighter draft text.")

    def test_reflect_keeps_original_on_empty_model(self):
        orig = fc.ollama_generate
        fc.ollama_generate = lambda *a, **k: ""        # model failed/empty
        try:
            draft = "Keep me: a perfectly good original draft of reasonable length."
            out = fc.reflect(draft, task="draft")
        finally:
            fc.ollama_generate = orig
        self.assertEqual(out, draft)

    def test_reflect_keeps_original_on_implausibly_short(self):
        orig = fc.ollama_generate
        fc.ollama_generate = lambda *a, **k: "ok"      # too short to be a real rewrite
        try:
            draft = "A reasonably long original draft that should not be replaced by 'ok'."
            out = fc.reflect(draft, task="draft")
        finally:
            fc.ollama_generate = orig
        self.assertEqual(out, draft)

    def test_reflect_noop_on_empty_input(self):
        self.assertEqual(fc.reflect("", task="x"), "")
        self.assertEqual(fc.reflect(None), None)


if __name__ == "__main__":
    unittest.main()

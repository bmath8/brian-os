#!/usr/bin/env python3
"""Tests for runtime/commands.py - the two-way command grammar (pure, no network)."""
import os, sys, glob, tempfile, unittest

_TMP = tempfile.mkdtemp(prefix="fleet_cmd_")
os.environ["FLEET_ROOT"] = _TMP
os.environ["FLEET_COMMS"] = os.path.join(_TMP, "comms")
os.environ["FLEET_LOGS"] = os.path.join(_TMP, "logs")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))
import fleet_common as fc   # noqa: E402
import srs                  # noqa: E402
import commands as cmd      # noqa: E402


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


class CommandTests(unittest.TestCase):
    def test_help_and_unknown(self):
        self.assertIn("/status", cmd.handle("/help"))
        self.assertIn("/help", cmd.handle("plain text"))     # non-command -> help
        self.assertIn("Unknown", cmd.handle("/frobnicate"))

    def test_queue_creates_task(self):
        out = cmd.handle("/queue Draft a thank-you note to the recruiter")
        self.assertIn("Queued", out)
        self.assertTrue(glob.glob(f"{fc.COMMS}/queue/*.md"))

    def test_approve_moves_file(self):
        _write(f"{fc.COMMS}/review/mytask__2026-06-18.md", "STATUS: NEEDS REVIEW\n")
        out = cmd.handle("/approve mytask")
        self.assertIn("approved", out)
        self.assertTrue(glob.glob(f"{fc.COMMS}/review/approved/mytask*"))

    def test_approve_no_match(self):
        self.assertIn("No pending review", cmd.handle("/approve nonexistent"))

    def test_grade_card(self):
        cards = {}
        cid = srs.add_question(cards, "What fixes the state.json race?")
        srs.save(cards)
        out = cmd.handle(f"/grade {cid} 1")
        self.assertIn("got it", out)
        self.assertEqual(srs.load()[cid]["box"], 2)

    def test_grade_bad_usage(self):
        self.assertIn("Usage", cmd.handle("/grade onlyid"))

    def test_snooze_sets_and_brief_respects(self):
        out = cmd.handle("/snooze finance 5")
        self.assertIn("Snoozed finance", out)
        self.assertIn("finance", fc.snoozed_agents())

    def test_status(self):
        fc.state_update("scout", {"last_run": "2026-06-18", "status": "ok",
                                  "summary": "x", "needs_human": []})
        self.assertIn("scout", cmd.handle("/status"))


if __name__ == "__main__":
    unittest.main()

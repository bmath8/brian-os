#!/usr/bin/env python3
"""Tests for runtime/srs.py - the spaced-repetition logic (pure, no model)."""
import os, sys, tempfile, datetime, unittest

_TMP = tempfile.mkdtemp(prefix="fleet_srs_")
os.environ["FLEET_ROOT"] = _TMP
os.environ["FLEET_COMMS"] = os.path.join(_TMP, "comms")
os.environ["FLEET_LOGS"] = os.path.join(_TMP, "logs")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))
import srs  # noqa: E402

T0 = datetime.date(2026, 6, 18)


class SrsTests(unittest.TestCase):
    def test_add_is_idempotent(self):
        cards = {}
        a = srs.add_question(cards, "What binds Ollama to 0.0.0.0?", today=T0)
        b = srs.add_question(cards, "what binds   ollama to 0.0.0.0?", today=T0)  # same, normalized
        self.assertEqual(a, b)
        self.assertEqual(len(cards), 1)

    def test_new_card_is_due_today(self):
        cards = {}
        srs.add_question(cards, "Q one?", today=T0)
        self.assertEqual(len(srs.due(cards, today=T0)), 1)

    def test_correct_promotes_and_defers(self):
        cards = {}
        cid = srs.add_question(cards, "Q?", today=T0)
        srs.grade(cards, cid, correct=True, today=T0)
        self.assertEqual(cards[cid]["box"], 2)
        # box 2 -> due in 2 days, so not due today
        self.assertEqual(srs.due(cards, today=T0), [])
        # but due again 2 days later
        self.assertEqual(len(srs.due(cards, today=T0 + datetime.timedelta(days=2))), 1)

    def test_wrong_resets_to_box1(self):
        cards = {}
        cid = srs.add_question(cards, "Q?", today=T0)
        srs.grade(cards, cid, correct=True, today=T0)
        srs.grade(cards, cid, correct=True, today=T0)   # box 3
        srs.grade(cards, cid, correct=False, today=T0)  # reset
        self.assertEqual(cards[cid]["box"], 1)

    def test_save_load_roundtrip(self):
        cards = {}
        srs.add_question(cards, "Persisted?", today=T0)
        srs.save(cards)
        self.assertEqual(len(srs.load()), 1)


if __name__ == "__main__":
    unittest.main()

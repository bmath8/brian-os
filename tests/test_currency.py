"""Currency agent tests - structure + the resilience invariant. Offline (no network)."""
import os, sys, tempfile, unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME = os.path.join(REPO, "runtime")
sys.path.insert(0, RUNTIME)
import currency_agent as cur


class TestCurrency(unittest.TestCase):
    def test_shipped_config_valid(self):
        # The real config in the repo must be valid JSON with the keys the agent maintains.
        # (load_cfg() itself reads from fc.ROOT, which the test harness may point at a temp dir.)
        import json
        cfg = json.load(open(os.path.join(REPO, "shared", "currency_watch.json"), encoding="utf-8"))
        self.assertIn("releases_watch", cfg)
        self.assertIn("auto_apply_allowlist", cfg)

    def test_load_cfg_returns_dict(self):
        self.assertIsInstance(cur.load_cfg(), dict)

    def test_classify(self):
        for fname, expect in (("package.json", "node"),
                              ("requirements.txt", "python"),
                              ("index.html", "static")):
            with tempfile.TemporaryDirectory() as d:
                open(os.path.join(d, fname), "w").write("x")
                self.assertEqual(cur.classify(d), expect)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cur.classify(d), "other")

    def test_discover_returns_list(self):
        self.assertIsInstance(cur.discover_repos(cur.load_cfg()), list)

    def test_run_never_raises(self):
        # the resilience invariant: run() returns (rc,out,err) and never throws,
        # so a failing external tool can never crash the cron job.
        rc, out, err = cur.run("exit 0")
        self.assertEqual(rc, 0)
        rc2, _, _ = cur.run("definitely-not-a-real-command-xyzzy-12345")
        self.assertNotEqual(rc2, 0)


if __name__ == "__main__":
    unittest.main()

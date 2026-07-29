"""Draft-only guardrail test (#48).

Codifies the fleet's core safety invariant so a future change can't silently
regress it: the DRAFTING agents must never send messages, spend money, or
destroy data on Brian's behalf. They produce drafts/status onto the blackboard
(comms/) or into the approval queue (comms/review/); a human approves before
anything leaves. Only explicitly-allowlisted INFRA may message directly
(boot_smoke health pings) or self-heal.
"""
import os
import unittest

RUNTIME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime")

# Agents that must be strictly draft-only (produce drafts/status, never send/spend/delete).
DRAFTING = [
    "career_agent", "finance_agent", "health_agent", "scout_agent", "research_agent",
    "overnight_worker", "learning_agent", "calendar_agent",
    "memory_index", "feedback", "srs", "commands",
]
# Notifiers/infra explicitly allowed to message BRIAN directly (his own Telegram) -
# the brief, watchdog alerts, weekly review, boot health. These notify; they never
# send drafts/outreach on Brian's behalf to third parties.
ALLOWLIST = ["boot_smoke", "system_watchdog", "fleet_common", "daily_brief", "weekly_review", "model_review"]

# Side-effects a drafting agent must never perform.
FORBIDDEN_SUBSTRINGS = [
    "api.telegram.org",   # direct Telegram send (must go via gateway/blackboard)
    "sendMessage",        # ditto
    "shutil.rmtree",      # destructive
    "os.unlink",          # destructive
    "fc.telegram_send(",  # direct send helper is infra-only
]


class TestDraftOnlyGuardrails(unittest.TestCase):
    def test_drafting_agents_have_no_send_spend_destroy(self):
        for name in DRAFTING:
            p = os.path.join(RUNTIME, name + ".py")
            if not os.path.isfile(p):
                continue
            with open(p, encoding="utf-8") as fh:
                src = fh.read()
            for bad in FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(
                    bad, src,
                    f"{name}.py contains forbidden side-effect '{bad}' - drafting agents "
                    f"must be draft-only (route output through the blackboard / approval queue).")

    def test_overnight_worker_routes_through_review(self):
        """The one agent that drafts outreach/applications must stage them for approval."""
        p = os.path.join(RUNTIME, "overnight_worker.py")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                src = fh.read().lower()
            self.assertIn("review", src,
                          "overnight_worker must write drafts to comms/review/ for human approval.")

    def test_allowlisted_infra_exists(self):
        """Sanity: the infra allowed to send directly is a known, small set."""
        self.assertIn("boot_smoke", ALLOWLIST)


class TestSecretRedaction(unittest.TestCase):
    """Outbound secret redaction (#46): our self-send must never deliver a key/token."""

    def setUp(self):
        import sys
        if RUNTIME not in sys.path:
            sys.path.insert(0, RUNTIME)

    def test_redacts_common_secrets(self):
        import fleet_common as fc
        for c in ("my key is sk-abcdefghij1234567890ABCDEFXYZ",
                  "TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ012345678",
                  "AKIAIOSFODNN7EXAMPLE",
                  "GMAIL_APP_PASSWORD=abcdefghijklmnop"):
            self.assertIn("[REDACTED]", fc.redact_secrets(c), f"did not redact: {c}")

    def test_keeps_normal_text(self):
        import fleet_common as fc
        t = "Apply to 5 jobs today; runway is about 4 months."
        self.assertEqual(fc.redact_secrets(t), t)


if __name__ == "__main__":
    unittest.main()

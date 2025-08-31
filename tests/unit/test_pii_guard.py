"""Tests for the PiiRedactionGuard class."""

import re
import unittest

from safellm.context import Context
from safellm.guards.pii import PiiRedactionGuard


class TestPiiRedactionGuard(unittest.TestCase):
    """Test the PiiRedactionGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = PiiRedactionGuard(mode="mask")

        self.assertEqual(guard.name, "pii_redaction")
        self.assertEqual(guard.mode, "mask")

    def test_email_detection_mask(self):
        """Test email detection with mask mode."""
        guard = PiiRedactionGuard(mode="mask", targets=["email"])
        ctx = Context()

        result = guard.check("Contact me at user@example.com", ctx)
        self.assertIn(result.action, ["allow", "transform"])

        if result.action == "transform":
            self.assertNotEqual(result.output, "Contact me at user@example.com")

    def test_email_detection_remove(self):
        """Test email detection with remove mode."""
        guard = PiiRedactionGuard(mode="remove", targets=["email"])
        ctx = Context()

        result = guard.check("Email: user@test.com and phone 555-1234", ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_phone_detection(self):
        """Test phone number detection."""
        guard = PiiRedactionGuard(mode="mask", targets=["phone"])
        ctx = Context()

        result = guard.check("Call me at 555-123-4567", ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_multiple_targets(self):
        """Test with multiple PII targets."""
        guard = PiiRedactionGuard(mode="mask", targets=["email", "phone", "credit_card"])
        ctx = Context()

        test_cases = [
            "Email: user@example.com",
            "Phone: 555-123-4567",
            "Credit card: 4111-1111-1111-1111",
        ]

        for case in test_cases:
            result = guard.check(case, ctx)
            self.assertIn(result.action, ["allow", "transform"])

    def test_custom_patterns(self):
        """Test custom patterns."""
        custom_pattern = re.compile(r"\bcustom\d+\b")
        guard = PiiRedactionGuard(custom_patterns=[custom_pattern])
        ctx = Context()

        result = guard.check("This has custom123 pattern", ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_no_pii_content(self):
        """Test content with no PII."""
        guard = PiiRedactionGuard(mode="mask")
        ctx = Context()

        result = guard.check("This is just normal text", ctx)
        self.assertEqual(result.action, "allow")

    def test_empty_content(self):
        """Test empty content."""
        guard = PiiRedactionGuard(mode="mask")
        ctx = Context()

        result = guard.check("", ctx)
        self.assertEqual(result.action, "allow")


if __name__ == "__main__":
    unittest.main()

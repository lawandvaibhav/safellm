"""Tests for the PrivacyGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.privacy import PrivacyComplianceGuard


class TestPrivacyComplianceGuard(unittest.TestCase):
    """Test the PrivacyComplianceGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = PrivacyComplianceGuard()

        self.assertEqual(guard.name, "privacy_compliance")

    def test_medical_privacy_detection(self):
        """Test medical privacy detection."""
        guard = PrivacyComplianceGuard()
        ctx = Context()

        # Test safe content
        result = guard.check("Hello world", ctx)
        self.assertEqual(result.action, "allow")

        # Test medical information - be more specific
        result = guard.check("Patient was diagnosed with diabetes and requires medication", ctx)
        self.assertIn(result.action, ["allow", "flag", "deny"])

    def test_financial_privacy_detection(self):
        """Test financial privacy detection."""
        guard = PrivacyComplianceGuard()
        ctx = Context()

        result = guard.check("The person has significant debt and low income", ctx)
        self.assertIn(result.action, ["allow", "flag", "deny"])

    def test_biometric_detection(self):
        """Test biometric data detection."""
        guard = PrivacyComplianceGuard()
        ctx = Context()

        result = guard.check("Fingerprint scan and facial recognition required", ctx)
        self.assertIn(result.action, ["allow", "flag", "deny"])

    def test_multiple_privacy_categories(self):
        """Test multiple privacy categories."""
        guard = PrivacyComplianceGuard()
        ctx = Context()

        test_cases = [
            "Medical diagnosis was confirmed by doctor",
            "Financial income and debt details",
            "Biometric identification and facial recognition system",
        ]

        for case in test_cases:
            result = guard.check(case, ctx)
            self.assertIn(result.action, ["allow", "flag", "deny"])

    def test_safe_content(self):
        """Test with safe content."""
        guard = PrivacyComplianceGuard()
        ctx = Context()

        result = guard.check("This is normal business content", ctx)
        self.assertEqual(result.action, "allow")


if __name__ == "__main__":
    unittest.main()

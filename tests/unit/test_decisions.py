"""Tests for decision types and validation errors."""

import unittest

from safellm.decisions import Decision, ValidationError


class TestDecision(unittest.TestCase):
    """Test the Decision class and its factory methods."""

    def test_allow_decision(self):
        """Test creating an allow decision."""
        data = {"test": "data"}
        decision = Decision.allow(data)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "allow")
        self.assertEqual(decision.reasons, [])
        self.assertEqual(decision.evidence, {})
        self.assertEqual(decision.output, data)
        self.assertIsNotNone(decision.audit_id)

    def test_allow_decision_with_evidence(self):
        """Test creating an allow decision with evidence."""
        data = "test"
        evidence = {"test": True}
        audit_id = "test-audit-id"

        decision = Decision.allow(data, audit_id=audit_id, evidence=evidence)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "allow")
        self.assertEqual(decision.evidence, evidence)
        self.assertEqual(decision.audit_id, audit_id)

    def test_deny_decision(self):
        """Test creating a deny decision."""
        data = "bad data"
        reasons = ["Invalid format", "Contains forbidden content"]

        decision = Decision.deny(data, reasons)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, "deny")
        self.assertEqual(decision.reasons, reasons)
        self.assertEqual(decision.output, data)
        self.assertIsNotNone(decision.audit_id)

    def test_transform_decision(self):
        """Test creating a transform decision."""
        original = "Original data with secrets"
        transformed = "Original data with ****"
        reasons = ["Masked secrets"]

        decision = Decision.transform(original, transformed, reasons)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "transform")
        self.assertEqual(decision.reasons, reasons)
        self.assertEqual(decision.output, transformed)
        self.assertIsNotNone(decision.audit_id)

    def test_retry_decision(self):
        """Test creating a retry decision."""
        data = "ambiguous data"
        reasons = ["Needs clarification"]

        decision = Decision.retry(data, reasons)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, "retry")
        self.assertEqual(decision.reasons, reasons)
        self.assertEqual(decision.output, data)
        self.assertIsNotNone(decision.audit_id)


class TestValidationError(unittest.TestCase):
    """Test the ValidationError exception."""

    def test_validation_error_creation(self):
        """Test creating a ValidationError from a decision."""
        reasons = ["Invalid input", "Format error"]
        decision = Decision.deny("bad data", reasons)

        error = ValidationError(decision)

        self.assertEqual(error.decision, decision)
        self.assertEqual(error.audit_id, decision.audit_id)
        self.assertEqual(error.reasons, reasons)
        self.assertEqual(error.evidence, decision.evidence)
        self.assertEqual(str(error), "Invalid input; Format error")

    def test_validation_error_single_reason(self):
        """Test ValidationError with a single reason."""
        decision = Decision.deny("data", ["Single error"])
        error = ValidationError(decision)

        self.assertEqual(str(error), "Single error")

    def test_validation_error_no_reasons(self):
        """Test ValidationError with no reasons."""
        decision = Decision.deny("data", [])
        error = ValidationError(decision)

        self.assertEqual(str(error), "")


if __name__ == "__main__":
    unittest.main()

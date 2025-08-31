"""Tests for the BusinessRulesGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.business import BusinessRulesGuard


class TestBusinessRulesGuard(unittest.TestCase):
    """Test the BusinessRulesGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        rules = [
            {
                "id": "test_rule_1",
                "name": "Length Check",
                "type": "length",
                "config": {
                    "min_length": 5,
                    "max_length": 100,
                },
            }
        ]
        guard = BusinessRulesGuard(rules=rules)

        self.assertEqual(guard.name, "business_rules")
        self.assertEqual(len(guard.rules), 1)

    def test_simple_rule(self):
        """Test with a simple rule."""
        rules = [
            {
                "id": "min_length",
                "name": "Minimum Length Rule",
                "type": "length",
                "config": {
                    "min_length": 5,
                },
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        # Test passing rule
        result = guard.check("Hello World", ctx)
        self.assertEqual(result.action, "allow")

        # Test failing rule
        result = guard.check("Hi", ctx)
        self.assertEqual(result.action, "deny")

    def test_multiple_rules(self):
        """Test with multiple rules."""
        rules = [
            {
                "id": "min_length",
                "name": "Minimum Length",
                "type": "length",
                "config": {
                    "min_length": 3,
                },
            },
            {
                "id": "no_test",
                "name": "No Test Word",
                "type": "pattern",
                "config": {"pattern": r"\btest\b", "match_required": False},
            },
        ]
        guard = BusinessRulesGuard(rules=rules, require_all=True)
        ctx = Context()

        # Test all rules pass
        result = guard.check("Hello World", ctx)
        self.assertEqual(result.action, "allow")

        # Test one rule fails
        result = guard.check("test data", ctx)
        self.assertEqual(result.action, "deny")

    def test_empty_rules(self):
        """Test with empty rules list."""
        guard = BusinessRulesGuard(rules=[])
        ctx = Context()

        result = guard.check("Any text", ctx)
        # With no rules and require_all=False, no rules pass so it should deny
        self.assertEqual(result.action, "deny")


if __name__ == "__main__":
    unittest.main()

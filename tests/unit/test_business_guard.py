"""Tests for the BusinessRulesGuard class."""

import unittest
from datetime import datetime, timedelta

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

    def test_initialization_with_action_and_require_all(self):
        """Test guard initialization with different parameters."""
        rules = [
            {
                "id": "test_rule_1",
                "name": "Length Check",
                "type": "length",
                "config": {"min_length": 5, "max_length": 100},
            }
        ]

        # Test block action (default)
        guard = BusinessRulesGuard(rules=rules, action="block", require_all=True)
        self.assertEqual(guard.action, "block")
        self.assertTrue(guard.require_all)

        # Test transform action
        guard = BusinessRulesGuard(rules=rules, action="transform")
        self.assertEqual(guard.action, "transform")

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

    def test_require_all_false_with_multiple_rules(self):
        """Test require_all=False - should pass if any rule passes."""
        rules = [
            {
                "id": "short_length",
                "name": "Short Length",
                "type": "length",
                "config": {"max_length": 2},  # This will fail
            },
            {
                "id": "min_length",
                "name": "Min Length",
                "type": "length",
                "config": {"min_length": 3},  # This will pass
            },
        ]
        guard = BusinessRulesGuard(rules=rules, require_all=False)
        ctx = Context()

        result = guard.check("Hello", ctx)
        self.assertEqual(result.action, "allow")  # Should pass because one rule passes

    def test_range_rule(self):
        """Test range validation rule."""
        rules = [
            {
                "id": "age_range",
                "name": "Age Range",
                "type": "range",
                "config": {"min": 18, "max": 100},
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        # Test valid range
        result = guard.check(25, ctx)
        self.assertEqual(result.action, "allow")

        # Test below range
        result = guard.check(15, ctx)
        self.assertEqual(result.action, "deny")

        # Test above range
        result = guard.check(150, ctx)
        self.assertEqual(result.action, "deny")

    def test_pattern_rule_match_required(self):
        """Test pattern rule with match_required=True."""
        rules = [
            {
                "id": "email_pattern",
                "name": "Email Pattern",
                "type": "pattern",
                "config": {
                    "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                    "match_required": True,
                },
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        # Test with email (should pass)
        result = guard.check("Contact us at test@example.com", ctx)
        self.assertEqual(result.action, "allow")

        # Test without email (should fail)
        result = guard.check("Contact us at our office", ctx)
        self.assertEqual(result.action, "deny")

    def test_time_window_rule(self):
        """Test time window rule."""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow() + timedelta(hours=1)

        rules = [
            {
                "id": "business_hours",
                "name": "Business Hours",
                "type": "time_window",
                "config": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                },
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        # Test within time window
        result = guard.check("Any data", ctx)
        self.assertEqual(result.action, "allow")

    def test_value_list_rule_whitelist(self):
        """Test value list rule with whitelist."""
        rules = [
            {
                "id": "allowed_values",
                "name": "Allowed Values",
                "type": "value_list",
                "config": {
                    "allowed_values": ["approved", "pending", "rejected"],
                },
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        # Test approved value
        result = guard.check("approved", ctx)
        self.assertEqual(result.action, "allow")

        # Test unapproved value
        result = guard.check("unknown", ctx)
        self.assertEqual(result.action, "deny")

    def test_value_list_rule_blacklist(self):
        """Test value list rule with blacklist."""
        rules = [
            {
                "id": "blocked_values",
                "name": "Blocked Values",
                "type": "value_list",
                "config": {
                    "forbidden_values": ["blocked", "forbidden"],
                },
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        # Test allowed value
        result = guard.check("allowed", ctx)
        self.assertEqual(result.action, "allow")

        # Test blocked value
        result = guard.check("blocked", ctx)
        self.assertEqual(result.action, "deny")

    def test_custom_rule(self):
        """Test custom rule with lambda function."""
        rules = [
            {
                "id": "even_number",
                "name": "Even Number",
                "type": "custom",
                "config": {
                    "error_message": "Number must be even",
                },
                "validator": lambda data, ctx, config: data % 2 == 0,
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        # Test even number
        result = guard.check(4, ctx)
        self.assertEqual(result.action, "allow")

        # Test odd number
        result = guard.check(5, ctx)
        self.assertEqual(result.action, "deny")

    def test_rule_exceptions(self):
        """Test handling of rule evaluation exceptions."""
        rules = [
            {
                "id": "error_rule",
                "name": "Error Rule",
                "type": "custom",
                "config": {},
                "validator": lambda data, ctx, config: 1 / 0,  # Will raise ZeroDivisionError
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        result = guard.check("any data", ctx)
        self.assertEqual(result.action, "deny")
        # Check that the error message is in the rule result
        rule_result = result.evidence["rule_results"][0]
        self.assertIn("Custom rule error:", rule_result["message"])

    def test_block_action(self):
        """Test block action mode."""
        rules = [
            {
                "id": "test_rule",
                "name": "Test Rule",
                "type": "length",
                "config": {"min_length": 10},
            }
        ]
        guard = BusinessRulesGuard(rules=rules, action="block")
        ctx = Context()

        result = guard.check("short", ctx)
        self.assertEqual(result.action, "deny")

    def test_transform_action(self):
        """Test transform action mode."""
        rules = [
            {
                "id": "transform_rule",
                "name": "Transform Rule",
                "type": "pattern",
                "config": {
                    "pattern": r"bad",
                    "match_required": False,
                    "replacement": "good",
                },
            }
        ]
        guard = BusinessRulesGuard(rules=rules, action="transform")
        ctx = Context()

        result = guard.check("This is bad text", ctx)
        self.assertEqual(result.action, "deny")  # No transformations available, falls back to deny
        self.assertIn("No transformations available", result.reasons)

    def test_validation_errors(self):
        """Test rule validation errors."""
        # Test missing required fields
        with self.assertRaises(ValueError):
            BusinessRulesGuard([{"id": "test"}])  # Missing name and type

        # Test invalid rule type
        with self.assertRaises(ValueError):
            BusinessRulesGuard([
                {
                    "id": "test",
                    "name": "Test",
                    "type": "invalid_type",
                    "config": {}
                }
            ])

    def test_comprehensive_evidence(self):
        """Test that evidence contains all expected information."""
        rules = [
            {
                "id": "length_check",
                "name": "Length Check",
                "type": "length",
                "config": {"min_length": 5, "max_length": 20},
            },
            {
                "id": "pattern_check",
                "name": "Pattern Check",
                "type": "pattern",
                "config": {"pattern": r"test", "match_required": False},
            }
        ]
        guard = BusinessRulesGuard(rules=rules, require_all=True)
        ctx = Context()

        result = guard.check("Hello World", ctx)

        # Check evidence structure
        evidence = result.evidence
        self.assertIn("rules_evaluated", evidence)
        self.assertIn("rules_passed", evidence)
        self.assertIn("rules_failed", evidence)
        self.assertIn("require_all_rules", evidence)
        self.assertIn("overall_passed", evidence)
        self.assertIn("rule_results", evidence)
        self.assertIn("passed_rule_ids", evidence)
        self.assertIn("failed_rule_ids", evidence)

        self.assertEqual(evidence["rules_evaluated"], 2)
        self.assertTrue(evidence["require_all_rules"])

    def test_non_string_data_handling(self):
        """Test handling of non-string data types."""
        rules = [
            {
                "id": "length_rule",
                "name": "Length Rule",
                "type": "length",
                "config": {"min_length": 2},
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        # Test with list
        result = guard.check([1, 2, 3], ctx)
        self.assertEqual(result.action, "allow")

        # Test with dict
        result = guard.check({"a": "b"}, ctx)  # str() gives "{'a': 'b'}" which is 10 chars
        self.assertEqual(result.action, "allow")  # Length > 2, so passes

        # Test with short input that should fail
        result = guard.check("a", ctx)  # Length 1 < min_length 2
        self.assertEqual(result.action, "deny")

    def test_case_sensitivity_in_patterns(self):
        """Test case sensitivity in pattern rules."""
        rules = [
            {
                "id": "case_sensitive",
                "name": "Case Sensitive",
                "type": "pattern",
                "config": {
                    "pattern": r"Test",
                    "match_required": True,
                    "case_sensitive": True,
                },
            }
        ]
        guard = BusinessRulesGuard(rules=rules)
        ctx = Context()

        # Test exact case match
        result = guard.check("Test data", ctx)
        self.assertEqual(result.action, "allow")

        # Test wrong case
        result = guard.check("test data", ctx)
        self.assertEqual(result.action, "deny")

    def test_rule_message_truncation(self):
        """Test that failure reasons are properly truncated."""
        rules = []
        for i in range(10):  # Create many failing rules
            rules.append({
                "id": f"rule_{i}",
                "name": f"Rule {i}",
                "type": "length",
                "config": {"min_length": 100},  # Will fail for short text
            })

        guard = BusinessRulesGuard(rules=rules, require_all=True)
        ctx = Context()

        result = guard.check("short", ctx)
        self.assertEqual(result.action, "deny")

        # Check that reasons are truncated
        reasons = result.reasons
        failed_rule_reasons = [r for r in reasons if r.startswith("Failed:")]
        self.assertLessEqual(len(failed_rule_reasons), 3)

        # Should have "... and X more" message
        more_message = [r for r in reasons if "and" in r and "more" in r]
        if len(rules) > 3:
            self.assertTrue(len(more_message) > 0)


if __name__ == "__main__":
    unittest.main()

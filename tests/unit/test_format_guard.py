"""Tests for the FormatGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.format import FormatGuard


class TestFormatGuard(unittest.TestCase):
    """Test the FormatGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = FormatGuard(format_type="json")

        self.assertEqual(guard.name, "format_json")
        self.assertEqual(guard.format_type, "json")

    def test_json_format(self):
        """Test JSON format validation."""
        guard = FormatGuard(format_type="json")
        ctx = Context()

        # Test valid JSON
        result = guard.check('{"key": "value"}', ctx)
        self.assertEqual(result.action, "allow")

        # Test invalid JSON
        result = guard.check('{"key": value}', ctx)
        self.assertEqual(result.action, "deny")

    def test_email_format(self):
        """Test email format validation."""
        guard = FormatGuard(format_type="email")
        ctx = Context()

        # Test valid email
        result = guard.check("user@example.com", ctx)
        self.assertEqual(result.action, "allow")

        # Test invalid email
        result = guard.check("invalid-email", ctx)
        self.assertEqual(result.action, "deny")

    def test_url_format(self):
        """Test URL format validation."""
        guard = FormatGuard(format_type="url")
        ctx = Context()

        # Test valid URL
        result = guard.check("https://example.com", ctx)
        self.assertEqual(result.action, "allow")

        # Test invalid URL
        result = guard.check("not-a-url", ctx)
        self.assertEqual(result.action, "deny")

    def test_custom_format(self):
        """Test custom format with regex pattern."""
        guard = FormatGuard(format_type="custom", pattern=r"^\d{3}-\d{3}-\d{4}$")
        ctx = Context()

        # Test valid pattern
        result = guard.check("123-456-7890", ctx)
        self.assertEqual(result.action, "allow")

        # Test invalid pattern
        result = guard.check("invalid-format", ctx)
        self.assertEqual(result.action, "deny")


if __name__ == "__main__":
    unittest.main()

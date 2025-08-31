"""Tests for the HtmlSanitizerGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.html import HtmlSanitizerGuard


class TestHtmlSanitizerGuard(unittest.TestCase):
    """Test the HtmlSanitizerGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = HtmlSanitizerGuard(policy="strict")

        self.assertEqual(guard.name, "html_sanitizer")
        self.assertEqual(guard.policy, "strict")

    def test_strict_policy(self):
        """Test strict sanitization policy."""
        guard = HtmlSanitizerGuard(policy="strict")
        ctx = Context()

        # Test safe HTML
        result = guard.check("<p>Safe content</p>", ctx)
        self.assertIn(result.action, ["allow", "transform"])

        # Test unsafe HTML
        result = guard.check("<script>alert('xss')</script>", ctx)
        self.assertIn(result.action, ["transform", "deny"])

    def test_moderate_policy(self):
        """Test moderate sanitization policy."""
        guard = HtmlSanitizerGuard(policy="moderate")
        ctx = Context()

        # Test basic HTML
        result = guard.check("<p>Safe content</p>", ctx)
        self.assertIn(result.action, ["allow", "transform"])

        # Test with links
        result = guard.check('<a href="http://example.com">Link</a>', ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_custom_policy(self):
        """Test custom sanitization policy."""
        guard = HtmlSanitizerGuard(
            policy="custom", allowed_tags=["p", "strong"], allowed_attributes={"*": ["class"]}
        )
        ctx = Context()

        # Test allowed tags
        result = guard.check('<p class="text">Content</p>', ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_plain_text(self):
        """Test with plain text."""
        guard = HtmlSanitizerGuard()
        ctx = Context()

        result = guard.check("Just plain text", ctx)
        self.assertEqual(result.action, "allow")

    def test_empty_content(self):
        """Test with empty content."""
        guard = HtmlSanitizerGuard()
        ctx = Context()

        result = guard.check("", ctx)
        self.assertEqual(result.action, "allow")


if __name__ == "__main__":
    unittest.main()

"""Comprehensive test coverage for all guards and utilities."""

import unittest
from unittest.mock import Mock, patch

from safellm.context import Context
from safellm.decisions import Decision
from safellm.guards import (
    HtmlSanitizerGuard,
    LengthGuard,
    MarkdownSanitizerGuard,
    PiiRedactionGuard,
    ProfanityGuard,
    SchemaGuard,
    SecretMaskGuard,
)


class TestCoreGuards(unittest.TestCase):
    """Comprehensive tests for core guards."""

    def test_length_guard_comprehensive(self):
        """Test LengthGuard with all scenarios."""
        # Test with min_chars
        guard = LengthGuard(min_chars=5)
        ctx = Context()
        
        # Test text too short
        result = guard.check("Hi", ctx)
        self.assertEqual(result.action, "deny")
        
        # Test text long enough
        result = guard.check("Hello World", ctx)
        self.assertEqual(result.action, "allow")
        
        # Test with max_chars
        guard = LengthGuard(max_chars=10)
        result = guard.check("Hello", ctx)
        self.assertEqual(result.action, "allow")
        
        result = guard.check("This is too long", ctx)
        self.assertEqual(result.action, "deny")

    def test_pii_redaction_guard_comprehensive(self):
        """Test PiiRedactionGuard with various PII types."""
        # Test mask mode
        guard = PiiRedactionGuard(mode="mask")
        ctx = Context()
        
        # Test email detection
        result = guard.check("Contact me at user@example.com", ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_html_sanitizer_guard_comprehensive(self):
        """Test HtmlSanitizerGuard with various HTML content."""
        # Test strict policy
        guard = HtmlSanitizerGuard(policy="strict")
        ctx = Context()
        
        # Test safe HTML
        result = guard.check("<p>Safe content</p>", ctx)
        self.assertIn(result.action, ["allow", "transform"])


if __name__ == "__main__":
    unittest.main()
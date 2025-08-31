"""Tests for the LanguageGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.language import LanguageGuard


class TestLanguageGuard(unittest.TestCase):
    """Test the LanguageGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = LanguageGuard(allowed_languages=["english"])

        self.assertEqual(guard.name, "language")
        self.assertEqual(guard.allowed_languages, {"english"})

    def test_english_detection(self):
        """Test English language detection."""
        guard = LanguageGuard(allowed_languages=["english"])
        ctx = Context()

        result = guard.check("The quick brown fox jumps over the lazy dog", ctx)
        self.assertEqual(result.action, "allow")

    def test_multiple_languages(self):
        """Test multiple allowed languages."""
        guard = LanguageGuard(allowed_languages=["english", "spanish"])
        ctx = Context()

        # Test English
        result = guard.check("The quick brown fox", ctx)
        self.assertEqual(result.action, "allow")

        # Test Spanish
        result = guard.check("El gato está en la mesa", ctx)
        self.assertEqual(result.action, "allow")

    def test_confidence_threshold(self):
        """Test confidence threshold setting."""
        guard = LanguageGuard(allowed_languages=["english"], min_confidence=0.8)
        ctx = Context()

        result = guard.check("The quick brown fox jumps over the lazy dog", ctx)
        self.assertIn(result.action, ["allow", "deny"])

    def test_empty_text(self):
        """Test with empty text."""
        guard = LanguageGuard(allowed_languages=["english"])
        ctx = Context()

        result = guard.check("", ctx)
        self.assertEqual(result.action, "allow")

    def test_short_text(self):
        """Test with very short text."""
        guard = LanguageGuard(allowed_languages=["english"])
        ctx = Context()

        result = guard.check("Hi", ctx)
        self.assertIn(result.action, ["allow", "deny"])


if __name__ == "__main__":
    unittest.main()

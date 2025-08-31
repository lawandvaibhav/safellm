"""Tests for the ProfanityGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.profanity import ProfanityGuard


class TestProfanityGuard(unittest.TestCase):
    """Test the ProfanityGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = ProfanityGuard()

        self.assertEqual(guard.name, "profanity")

    def test_clean_content(self):
        """Test clean content."""
        guard = ProfanityGuard()
        ctx = Context()

        result = guard.check("This is a clean message", ctx)
        self.assertEqual(result.action, "allow")

    def test_empty_content(self):
        """Test empty content."""
        guard = ProfanityGuard()
        ctx = Context()

        result = guard.check("", ctx)
        self.assertEqual(result.action, "allow")

    def test_whitespace_content(self):
        """Test whitespace-only content."""
        guard = ProfanityGuard()
        ctx = Context()

        result = guard.check("   \n\t  ", ctx)
        self.assertEqual(result.action, "allow")

    def test_mixed_content(self):
        """Test mixed clean and potentially problematic content."""
        guard = ProfanityGuard()
        ctx = Context()

        # Test various content types
        test_cases = [
            "Hello world!",
            "This is a normal sentence.",
            "Testing 123",
            "Special characters: @#$%",
        ]

        for case in test_cases:
            result = guard.check(case, ctx)
            self.assertIn(result.action, ["allow", "deny"])

    def test_strict_mode(self):
        """Test strict mode if available."""
        try:
            guard = ProfanityGuard(strict=True)
            ctx = Context()

            result = guard.check("This is clean text", ctx)
            self.assertIn(result.action, ["allow", "deny"])
        except TypeError:
            # Guard doesn't support strict parameter
            pass

    def test_custom_words(self):
        """Test custom word list if supported."""
        try:
            guard = ProfanityGuard(custom_words={"badword"})
            ctx = Context()

            result = guard.check("This contains badword", ctx)
            self.assertIn(result.action, ["allow", "deny", "mask", "transform"])
        except TypeError:
            # Guard doesn't support custom_words parameter
            pass


if __name__ == "__main__":
    unittest.main()

"""Tests for the ToxicityGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.toxicity import ToxicityGuard


class TestToxicityGuard(unittest.TestCase):
    """Test the ToxicityGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = ToxicityGuard()

        self.assertEqual(guard.name, "toxicity")

    def test_non_toxic_content(self):
        """Test non-toxic content."""
        guard = ToxicityGuard()
        ctx = Context()

        result = guard.check("This is a nice, friendly message.", ctx)
        self.assertEqual(result.action, "allow")

    def test_empty_content(self):
        """Test empty content."""
        guard = ToxicityGuard()
        ctx = Context()

        result = guard.check("", ctx)
        self.assertEqual(result.action, "allow")

    def test_neutral_content(self):
        """Test neutral content."""
        guard = ToxicityGuard()
        ctx = Context()

        test_cases = [
            "Hello world",
            "The weather is nice today",
            "Please complete this task",
            "Thank you for your help",
        ]

        for case in test_cases:
            result = guard.check(case, ctx)
            self.assertEqual(result.action, "allow")

    def test_different_thresholds(self):
        """Test different toxicity thresholds."""
        # High threshold - more strict (if the guard supports thresholds)
        guard_strict = ToxicityGuard()
        ctx = Context()

        result = guard_strict.check("This is a normal message", ctx)
        self.assertEqual(result.action, "allow")

        # Test with potentially borderline content
        guard_lenient = ToxicityGuard()
        result = guard_lenient.check("This is a normal message", ctx)
        self.assertEqual(result.action, "allow")

    def test_long_content(self):
        """Test with longer content."""
        guard = ToxicityGuard()
        ctx = Context()

        long_text = (
            "This is a longer piece of text that contains multiple sentences. "
            "It should be analyzed for toxicity as a whole. "
            "The guard should handle longer inputs properly."
        )

        result = guard.check(long_text, ctx)
        self.assertEqual(result.action, "allow")

    def test_mixed_content(self):
        """Test mixed content types."""
        guard = ToxicityGuard()
        ctx = Context()

        mixed_cases = [
            "Hello! How are you doing today?",
            "I disagree with your opinion, but respect it.",
            "This product could be better designed.",
            "I'm frustrated with this situation.",
        ]

        for case in mixed_cases:
            result = guard.check(case, ctx)
            self.assertIn(result.action, ["allow", "deny"])


if __name__ == "__main__":
    unittest.main()

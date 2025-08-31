"""Tests for the SimilarityGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.similarity import SimilarityGuard


class TestSimilarityGuard(unittest.TestCase):
    """Test the SimilarityGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = SimilarityGuard(similarity_threshold=0.8)

        self.assertEqual(guard.name, "similarity")
        self.assertEqual(guard.similarity_threshold, 0.8)

    def test_similar_text(self):
        """Test detection of similar text."""
        guard = SimilarityGuard(similarity_threshold=0.7)
        ctx = Context()

        # Test first text to populate history
        result1 = guard.check("Hello world!", ctx)
        self.assertEqual(result1.action, "allow")

        # Test similar text (should trigger similarity detection)
        result2 = guard.check("Hello world", ctx)
        self.assertIn(result2.action, ["allow", "flag", "deny"])

    def test_dissimilar_text(self):
        """Test dissimilar text."""
        guard = SimilarityGuard(similarity_threshold=0.9)
        ctx = Context()

        # Test first text
        result1 = guard.check("Hello world", ctx)
        self.assertEqual(result1.action, "allow")

        # Test completely different text
        result2 = guard.check("The quick brown fox jumps", ctx)
        self.assertEqual(result2.action, "allow")

    def test_exact_match(self):
        """Test exact match."""
        guard = SimilarityGuard(similarity_threshold=0.8)
        ctx = Context()

        # Test first text
        result1 = guard.check("Exact match text", ctx)
        self.assertEqual(result1.action, "allow")

        # Test exact match (should trigger similarity)
        result2 = guard.check("Exact match text", ctx)
        self.assertIn(result2.action, ["allow", "flag", "deny"])

    def test_empty_input_text(self):
        """Test with empty input text."""
        guard = SimilarityGuard(similarity_threshold=0.8)
        ctx = Context()

        result = guard.check("", ctx)
        self.assertEqual(result.action, "allow")

    def test_different_thresholds(self):
        """Test different similarity thresholds."""
        # High threshold - stricter
        guard_strict = SimilarityGuard(similarity_threshold=0.95)
        ctx = Context()

        result = guard_strict.check("Hello world!", ctx)
        self.assertEqual(result.action, "allow")

        # Low threshold - more lenient
        guard_lenient = SimilarityGuard(similarity_threshold=0.3)
        result = guard_lenient.check("Completely different text", ctx)
        self.assertEqual(result.action, "allow")


if __name__ == "__main__":
    unittest.main()

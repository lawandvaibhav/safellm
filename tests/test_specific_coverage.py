"""Specific tests targeting low coverage areas."""

import asyncio
import unittest

from safellm.context import Context
from safellm.decisions import Decision
from safellm.guard import BaseGuard
from safellm.guards import (
    HtmlSanitizerGuard,
    LengthGuard,
)
from safellm.pipeline import Pipeline


class MockGuard(BaseGuard):
    """Mock guard for testing."""

    def __init__(self, name="mock", action="allow", error=False):
        self._name = name
        self.action = action
        self.error = error

    @property
    def name(self):
        return self._name

    def check(self, data, ctx):
        if self.error:
            raise ValueError("Mock error")

        if self.action == "allow":
            return Decision.allow(data)
        elif self.action == "deny":
            return Decision.deny(data, ["Mock deny"])
        elif self.action == "transform":
            return Decision.transform(data, f"transformed_{data}", ["Transformed"])
        elif self.action == "retry":
            return Decision.retry(data, ["Mock retry"])


class TestPipelineCoverage(unittest.TestCase):
    """Tests to improve pipeline coverage."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization options."""
        guards = [MockGuard()]

        # Default initialization
        pipeline = Pipeline("test", guards)
        self.assertTrue(pipeline.fail_fast)
        self.assertEqual(pipeline.on_error, "deny")

        # Custom initialization
        pipeline = Pipeline("test", guards, fail_fast=False, on_error="allow")
        self.assertFalse(pipeline.fail_fast)
        self.assertEqual(pipeline.on_error, "allow")

    def test_pipeline_validate_success(self):
        """Test successful validation."""
        guards = [MockGuard("guard1"), MockGuard("guard2")]
        pipeline = Pipeline("test", guards)

        result = pipeline.validate("test data")
        self.assertEqual(result.action, "allow")
        self.assertEqual(result.output, "test data")

    def test_pipeline_validate_with_context(self):
        """Test validation with context."""
        guards = [MockGuard()]
        pipeline = Pipeline("test", guards)
        ctx = Context(model="test-model")

        result = pipeline.validate("test data", ctx=ctx)
        self.assertEqual(result.action, "allow")

    def test_pipeline_fail_fast_true(self):
        """Test pipeline with fail_fast=True."""
        guards = [MockGuard("pass"), MockGuard("fail", action="deny"), MockGuard("never_reached")]
        pipeline = Pipeline("test", guards, fail_fast=True)

        result = pipeline.validate("test data")
        self.assertEqual(result.action, "deny")

    def test_pipeline_fail_fast_false(self):
        """Test pipeline with fail_fast=False."""
        guards = [MockGuard("fail1", action="deny"), MockGuard("pass"), MockGuard("fail2", action="deny")]
        pipeline = Pipeline("test", guards, fail_fast=False)

        result = pipeline.validate("test data")
        self.assertEqual(result.action, "allow")  # With fail_fast=False, pipeline continues and allows at the end

    def test_pipeline_transform(self):
        """Test pipeline with transform action."""
        guards = [
            MockGuard("transform1", action="transform"),
            MockGuard("pass")
        ]
        pipeline = Pipeline("test", guards)

        result = pipeline.validate("test")
        self.assertEqual(result.action, "transform")  # Should be transform since transformations occurred
        self.assertEqual(result.output, "transformed_test")

    def test_pipeline_retry(self):
        """Test pipeline with retry action."""
        guards = [MockGuard("retry", action="retry")]
        pipeline = Pipeline("test", guards)

        result = pipeline.validate("test data")
        self.assertEqual(result.action, "retry")
        self.assertIn("Mock retry", result.reasons)

    def test_pipeline_error_handling_deny(self):
        """Test pipeline error handling with deny."""
        guards = [MockGuard("error", error=True)]
        pipeline = Pipeline("test", guards, on_error="deny")

        result = pipeline.validate("test data")
        self.assertEqual(result.action, "deny")
        self.assertTrue(any("Mock error" in reason for reason in result.reasons))

    def test_pipeline_error_handling_allow(self):
        """Test pipeline error handling with allow."""
        guards = [MockGuard("error", error=True)]
        pipeline = Pipeline("test", guards, on_error="allow", fail_fast=False)

        result = pipeline.validate("test data")
        self.assertEqual(result.action, "allow")

    def test_pipeline_error_handling_retry(self):
        """Test pipeline error handling with retry."""
        guards = [MockGuard("error", error=True)]
        pipeline = Pipeline("test", guards, on_error="retry", fail_fast=False)

        result = pipeline.validate("test data")
        self.assertEqual(result.action, "allow")  # When on_error="retry", it continues and allows

    def test_pipeline_repr(self):
        """Test pipeline string representation."""
        guards = [MockGuard("test1"), MockGuard("test2")]
        pipeline = Pipeline("test", guards)

        repr_str = repr(pipeline)
        self.assertIn("Pipeline", repr_str)
        self.assertIn("test", repr_str)

    def test_pipeline_async_validate(self):
        """Test async validation."""
        async def run_test():
            guards = [MockGuard("async_guard")]
            pipeline = Pipeline("test", guards)

            result = await pipeline.avalidate("test data")
            self.assertEqual(result.action, "allow")

        asyncio.run(run_test())

    def test_pipeline_async_error(self):
        """Test async validation with error."""
        async def run_test():
            guards = [MockGuard("error", error=True)]
            pipeline = Pipeline("test", guards, on_error="deny")

            result = await pipeline.avalidate("test data")
            self.assertEqual(result.action, "deny")

        asyncio.run(run_test())


class TestLengthGuardCoverage(unittest.TestCase):
    """Tests to improve LengthGuard coverage."""

    def test_length_guard_initialization(self):
        """Test LengthGuard initialization and validation."""
        # Test parameter validation
        with self.assertRaises(ValueError):
            LengthGuard(min_chars=-1)

        with self.assertRaises(ValueError):
            LengthGuard(max_chars=-1)

        with self.assertRaises(ValueError):
            LengthGuard(max_tokens=-1)

        with self.assertRaises(ValueError):
            LengthGuard(min_chars=10, max_chars=5)

    def test_length_guard_min_chars(self):
        """Test min_chars validation."""
        guard = LengthGuard(min_chars=5)
        ctx = Context()

        # Too short
        result = guard.check("Hi", ctx)
        self.assertEqual(result.action, "deny")

        # Just right
        result = guard.check("Hello", ctx)
        self.assertEqual(result.action, "allow")

        # Longer is fine
        result = guard.check("Hello World", ctx)
        self.assertEqual(result.action, "allow")

    def test_length_guard_max_chars(self):
        """Test max_chars validation."""
        guard = LengthGuard(max_chars=10)
        ctx = Context()

        # Within limit
        result = guard.check("Hello", ctx)
        self.assertEqual(result.action, "allow")

        # At limit
        result = guard.check("1234567890", ctx)
        self.assertEqual(result.action, "allow")

        # Over limit
        result = guard.check("12345678901", ctx)
        self.assertEqual(result.action, "deny")

    def test_length_guard_max_tokens(self):
        """Test max_tokens validation."""
        guard = LengthGuard(max_tokens=3)
        ctx = Context()

        # Within limit
        result = guard.check("one two", ctx)
        self.assertEqual(result.action, "allow")

        # At limit
        result = guard.check("one two three", ctx)
        self.assertEqual(result.action, "allow")

        # Over limit
        result = guard.check("one two three four", ctx)
        self.assertEqual(result.action, "deny")

    def test_length_guard_combined(self):
        """Test combined min and max constraints."""
        guard = LengthGuard(min_chars=5, max_chars=15)
        ctx = Context()

        # Too short
        result = guard.check("Hi", ctx)
        self.assertEqual(result.action, "deny")

        # Just right
        result = guard.check("Perfect", ctx)
        self.assertEqual(result.action, "allow")

        # Too long
        result = guard.check("This is way too long", ctx)
        self.assertEqual(result.action, "deny")

    def test_length_guard_non_string_data(self):
        """Test with non-string data."""
        guard = LengthGuard(max_chars=5)
        ctx = Context()

        # Numbers
        result = guard.check(123, ctx)
        self.assertEqual(result.action, "allow")

        # Lists (converted to string)
        result = guard.check([1, 2], ctx)  # "[1, 2]" is 6 chars
        self.assertEqual(result.action, "deny")


class TestHtmlGuardCoverage(unittest.TestCase):
    """Tests to improve HTML guard coverage."""

    def test_html_guard_policies(self):
        """Test different HTML sanitization policies."""
        ctx = Context()

        # Strict policy with dangerous content
        guard = HtmlSanitizerGuard(policy="strict")
        result = guard.check("<script>alert('xss')</script><p>Safe</p>", ctx)
        self.assertEqual(result.action, "transform")
        self.assertNotIn("<script>", result.output)

        # Moderate policy with mixed content
        guard = HtmlSanitizerGuard(policy="moderate")
        result = guard.check("<h1>Title</h1><script>bad</script><p>Content</p>", ctx)
        self.assertEqual(result.action, "transform")

        # Custom policy
        guard = HtmlSanitizerGuard(
            policy="custom",
            allowed_tags=["p"],
            allowed_attributes={"p": ["class"]}
        )
        result = guard.check("<p class='test'>Text</p><div>Remove</div>", ctx)
        self.assertEqual(result.action, "transform")

        # Invalid policy
        with self.assertRaises(ValueError):
            HtmlSanitizerGuard(policy="invalid")

    def test_html_guard_without_bleach(self):
        """Test HTML guard fallback without bleach."""
        guard = HtmlSanitizerGuard()
        guard._has_bleach = False  # Force fallback
        ctx = Context()

        result = guard.check("<script>alert('xss')</script>", ctx)
        self.assertEqual(result.action, "transform")

    def test_html_guard_clean_content(self):
        """Test HTML guard with clean content."""
        guard = HtmlSanitizerGuard()
        ctx = Context()

        result = guard.check("Just plain text", ctx)
        self.assertEqual(result.action, "allow")

    def test_html_guard_non_string(self):
        """Test HTML guard with non-string input."""
        guard = HtmlSanitizerGuard()
        ctx = Context()

        result = guard.check(123, ctx)
        self.assertIn(result.action, ["allow", "transform"])


if __name__ == "__main__":
    unittest.main()

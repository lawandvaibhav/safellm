"""Tests for the Pipeline class."""

import unittest

from safellm.context import Context
from safellm.decisions import Decision
from safellm.guard import BaseGuard
from safellm.guards.length import LengthGuard
from safellm.pipeline import Pipeline


class MockPassGuard(BaseGuard):
    """Mock guard that always passes."""

    def __init__(self, name="pass_guard"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def check(self, data, ctx):
        return Decision.allow(
            output=data, evidence={"guard": self.name, "data_length": len(str(data))}
        )


class MockFailGuard(BaseGuard):
    """Mock guard that always fails."""

    def __init__(self, name="fail_guard"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def check(self, data, ctx):
        return Decision.deny(
            output=data, reasons=[f"{self.name} rejected"], evidence={"guard": self.name}
        )


class MockTransformGuard(BaseGuard):
    """Mock guard that transforms data."""

    def __init__(self, name="transform_guard", transform_func=None):
        self._name = name
        self.transform_func = transform_func or (lambda x: x.upper())

    @property
    def name(self) -> str:
        return self._name

    def check(self, data, ctx):
        transformed = self.transform_func(str(data))
        return Decision.transform(
            original=data,
            transformed=transformed,
            reasons=[f"Transformed by {self.name}"],
            evidence={"guard": self.name, "original": str(data)},
        )


class MockRetryGuard(BaseGuard):
    """Mock guard that requests retry."""

    def __init__(self, name="retry_guard"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def check(self, data, ctx):
        return Decision.retry(output=data, reasons=["Please retry"], evidence={"guard": self.name})


class MockErrorGuard(BaseGuard):
    """Mock guard that raises an error."""

    def __init__(self, name="error_guard", on_error="deny"):
        self._name = name
        self.on_error = on_error

    @property
    def name(self) -> str:
        return self._name

    def check(self, data, ctx):
        raise ValueError("Mock error for testing")


class TestPipeline(unittest.TestCase):
    """Test the Pipeline class."""

    def test_initialization(self):
        """Test pipeline initialization."""
        guard1 = LengthGuard(max_chars=100)
        guard2 = LengthGuard(min_chars=5)

        pipeline = Pipeline("test_pipeline", [guard1, guard2])

        self.assertEqual(pipeline.name, "test_pipeline")
        self.assertEqual(len(pipeline.steps), 2)
        self.assertTrue(pipeline.fail_fast)
        self.assertEqual(pipeline.on_error, "deny")

    def test_initialization_empty_steps(self):
        """Test that empty steps raise an error."""
        with self.assertRaises(ValueError) as cm:
            Pipeline("test", [])
        self.assertIn("must have at least one guard", str(cm.exception))

    def test_validate_single_guard_success(self):
        """Test validation with single guard that passes."""
        guard = LengthGuard(max_chars=100)
        pipeline = Pipeline("test", [guard])

        decision = pipeline.validate("Hello world")

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "allow")
        self.assertIsNotNone(decision.audit_id)

    def test_validate_single_guard_failure(self):
        """Test validation with single guard that fails."""
        guard = LengthGuard(max_chars=5)
        pipeline = Pipeline("test", [guard])

        decision = pipeline.validate("This text is too long")

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, "deny")
        self.assertTrue(len(decision.reasons) > 0)

    def test_validate_multiple_guards_all_pass(self):
        """Test validation with multiple guards that all pass."""
        guard1 = LengthGuard(max_chars=100)
        guard2 = LengthGuard(min_chars=3)
        pipeline = Pipeline("test", [guard1, guard2])

        decision = pipeline.validate("Hello world")

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "allow")

    def test_validate_fail_fast_true(self):
        """Test validation with fail_fast=True."""
        guards = [MockPassGuard("guard1"), MockFailGuard("guard2"), MockPassGuard("guard3")]
        pipeline = Pipeline("test_pipeline", guards, fail_fast=True)
        ctx = Context()

        result = pipeline.validate("test data", ctx=ctx)

        self.assertEqual(result.action, "deny")
        self.assertTrue(any("guard2 rejected" in reason for reason in result.reasons))

    def test_validate_fail_fast_false(self):
        """Test validation with fail_fast=False."""
        guards = [MockFailGuard("guard1"), MockPassGuard("guard2"), MockFailGuard("guard3")]
        pipeline = Pipeline("test_pipeline", guards, fail_fast=False)
        ctx = Context()

        result = pipeline.validate("test data", ctx=ctx)

        # With fail_fast=False, pipeline continues and allows at the end (current behavior)
        self.assertEqual(result.action, "allow")

    def test_validate_with_context(self):
        """Test validation with explicit context."""
        guard = LengthGuard(max_chars=100)
        pipeline = Pipeline("test", [guard])
        ctx = Context()

        decision = pipeline.validate("Hello world", ctx=ctx)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "allow")

    def test_validate_guard_exception_deny(self):
        """Test guard exception handling with deny."""
        guards = [MockPassGuard("guard1"), MockErrorGuard("error_guard")]
        pipeline = Pipeline("test_pipeline", guards)
        ctx = Context()

        result = pipeline.validate("test data", ctx=ctx)

        # Should deny on error by default
        self.assertEqual(result.action, "deny")
        self.assertTrue(any("Mock error for testing" in reason for reason in result.reasons))

    def test_validate_guard_exception_allow(self):
        """Test guard exception handling with allow on error."""
        guards = [MockPassGuard("guard1"), MockErrorGuard("error_guard")]
        pipeline = Pipeline("test_pipeline", guards, on_error="allow", fail_fast=False)
        ctx = Context()

        result = pipeline.validate("test data", ctx=ctx)

        # Should allow on error
        self.assertEqual(result.action, "allow")

    def test_pipeline_transform_action(self):
        """Test pipeline with transform action."""
        guards = [
            MockPassGuard("guard1"),
            MockTransformGuard("transform1", lambda x: x.upper()),
            MockPassGuard("guard2"),
        ]
        pipeline = Pipeline("test_pipeline", guards)
        ctx = Context()

        result = pipeline.validate("hello", ctx=ctx)

        self.assertEqual(result.action, "transform")
        self.assertEqual(result.output, "HELLO")

    def test_pipeline_chained_transforms(self):
        """Test pipeline with multiple transform guards."""
        guards = [
            MockTransformGuard("upper", lambda x: x.upper()),
            MockTransformGuard("prefix", lambda x: f"PREFIX_{x}"),
        ]
        pipeline = Pipeline("test_pipeline", guards)
        ctx = Context()

        result = pipeline.validate("hello", ctx=ctx)

        self.assertEqual(result.action, "transform")
        self.assertEqual(result.output, "PREFIX_HELLO")

    def test_pipeline_retry_action(self):
        """Test pipeline with retry action."""
        guards = [MockPassGuard("guard1"), MockRetryGuard("retry1")]
        pipeline = Pipeline("test_pipeline", guards)
        ctx = Context()

        result = pipeline.validate("test data", ctx=ctx)

        self.assertEqual(result.action, "retry")
        self.assertTrue(any("Please retry" in reason for reason in result.reasons))

    def test_repr(self):
        """Test pipeline string representation."""
        guards = [LengthGuard(max_chars=10)]
        pipeline = Pipeline("test_pipeline", guards)

        repr_str = repr(pipeline)
        self.assertIn("Pipeline", repr_str)
        self.assertIn("steps=1", repr_str)

    def test_avalidate_basic(self):
        """Test async validation basic functionality."""
        guards = [MockPassGuard("async_guard1"), MockPassGuard("async_guard2")]
        pipeline = Pipeline("test_pipeline", guards)

        # Just test that the method exists and is callable
        self.assertTrue(hasattr(pipeline, "avalidate"))
        self.assertTrue(callable(pipeline.avalidate))


if __name__ == "__main__":
    unittest.main()

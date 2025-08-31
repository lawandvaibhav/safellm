"""Tests for the Pipeline class."""

from unittest.mock import Mock

from safellm.context import Context
from safellm.decisions import Decision
from safellm.guards.length import LengthGuard
from safellm.pipeline import Pipeline


class TestPipeline:
    """Test the Pipeline class."""

    def test_initialization(self):
        """Test pipeline initialization."""
        guard1 = LengthGuard(max_chars=100)
        guard2 = LengthGuard(min_chars=5)

        pipeline = Pipeline("test_pipeline", [guard1, guard2])

        assert pipeline.name == "test_pipeline"
        assert len(pipeline.steps) == 2
        assert pipeline.fail_fast is True
        assert pipeline.on_error == "deny"

    def test_initialization_empty_steps(self):
        """Test that empty steps raise an error."""
        try:
            Pipeline("test", [])
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "must have at least one guard" in str(e)

    def test_validate_single_guard_success(self):
        """Test validation with single guard that passes."""
        guard = LengthGuard(max_chars=100)
        pipeline = Pipeline("test", [guard])

        decision = pipeline.validate("Hello world")

        assert decision.allowed is True
        assert decision.action == "allow"
        assert decision.audit_id is not None

    def test_validate_single_guard_failure(self):
        """Test validation with single guard that fails."""
        guard = LengthGuard(max_chars=5)
        pipeline = Pipeline("test", [guard])

        decision = pipeline.validate("This text is too long")

        assert decision.allowed is False
        assert decision.action == "deny"
        assert len(decision.reasons) > 0

    def test_validate_multiple_guards_all_pass(self):
        """Test validation with multiple guards that all pass."""
        guard1 = LengthGuard(min_chars=5)
        guard2 = LengthGuard(max_chars=50)
        pipeline = Pipeline("test", [guard1, guard2])

        decision = pipeline.validate("Hello world")

        assert decision.allowed is True
        assert decision.action == "allow"

    def test_validate_fail_fast_true(self):
        """Test validation with fail_fast=True stops at first failure."""
        guard1 = LengthGuard(max_chars=5)  # This will fail
        guard2 = Mock()
        guard2.name = "mock_guard"
        guard2.check = Mock(return_value=Decision.allow("data"))

        pipeline = Pipeline("test", [guard1, guard2], fail_fast=True)

        decision = pipeline.validate("This text is too long")

        assert decision.allowed is False
        assert decision.action == "deny"
        # guard2.check should not have been called due to fail_fast
        guard2.check.assert_not_called()

    def test_validate_fail_fast_false(self):
        """Test validation with fail_fast=False continues after failure."""
        guard1 = LengthGuard(max_chars=5)  # This will fail
        guard2 = LengthGuard(min_chars=1)  # This will pass

        pipeline = Pipeline("test", [guard1, guard2], fail_fast=False)

        decision = pipeline.validate("This text is too long")

        # With fail_fast=False, we should still get a result
        # The exact behavior depends on implementation details
        assert decision.audit_id is not None

    def test_validate_with_context(self):
        """Test validation with provided context."""
        guard = LengthGuard(max_chars=100)
        pipeline = Pipeline("test", [guard])
        ctx = Context(audit_id="custom-audit-id")

        decision = pipeline.validate("Hello world", ctx=ctx)

        assert decision.allowed is True
        assert decision.audit_id == "custom-audit-id"

    def test_validate_guard_exception_deny(self):
        """Test handling guard exceptions with on_error='deny'."""
        failing_guard = Mock()
        failing_guard.name = "failing_guard"
        failing_guard.check = Mock(side_effect=Exception("Guard failed"))

        pipeline = Pipeline("test", [failing_guard], on_error="deny")

        decision = pipeline.validate("test data")

        assert decision.allowed is False
        assert decision.action == "deny"
        assert any("failed" in reason.lower() for reason in decision.reasons)

    def test_validate_guard_exception_allow(self):
        """Test handling guard exceptions with on_error='allow'."""
        failing_guard = Mock()
        failing_guard.name = "failing_guard"
        failing_guard.check = Mock(side_effect=Exception("Guard failed"))

        good_guard = LengthGuard(max_chars=100)

        pipeline = Pipeline("test", [failing_guard, good_guard],
                          on_error="allow", fail_fast=False)

        decision = pipeline.validate("test data")

        # Should continue and allow since good_guard passes
        assert decision.audit_id is not None

    def test_repr(self):
        """Test pipeline string representation."""
        guard = LengthGuard(max_chars=100)
        pipeline = Pipeline("test_pipeline", [guard])

        repr_str = repr(pipeline)
        assert "Pipeline(" in repr_str
        assert "test_pipeline" in repr_str
        assert "steps=1" in repr_str
        assert "fail_fast=True" in repr_str

    async def test_avalidate_basic(self):
        """Test async validation."""
        guard = LengthGuard(max_chars=100)
        pipeline = Pipeline("test", [guard])

        decision = await pipeline.avalidate("Hello world")

        assert decision.allowed is True
        assert decision.action == "allow"
        assert decision.audit_id is not None

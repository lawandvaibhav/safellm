"""Tests for the Context class."""

from safellm.context import Context


class TestContext:
    """Test the Context class."""

    def test_default_initialization(self):
        """Test creating a context with default values."""
        ctx = Context()

        assert ctx.audit_id is not None
        assert ctx.model is None
        assert ctx.user_role is None
        assert ctx.purpose is None
        assert ctx.trace_id is None
        assert ctx.seed is None
        assert ctx.metadata == {}

    def test_full_initialization(self):
        """Test creating a context with all parameters."""
        ctx = Context(
            audit_id="test-audit",
            model="gpt-4",
            user_role="admin",
            purpose="content_generation",
            trace_id="trace-123",
            seed=42,
            metadata={"key": "value"},
        )

        assert ctx.audit_id == "test-audit"
        assert ctx.model == "gpt-4"
        assert ctx.user_role == "admin"
        assert ctx.purpose == "content_generation"
        assert ctx.trace_id == "trace-123"
        assert ctx.seed == 42
        assert ctx.metadata == {"key": "value"}

    def test_copy_no_overrides(self):
        """Test copying a context without overrides."""
        original = Context(audit_id="original-audit", model="gpt-3.5", metadata={"original": True})

        copy = original.copy()

        assert copy.audit_id == original.audit_id
        assert copy.model == original.model
        assert copy.metadata == original.metadata
        assert copy is not original  # Different objects

    def test_copy_with_overrides(self):
        """Test copying a context with overrides."""
        original = Context(
            audit_id="original-audit",
            model="gpt-3.5",
            user_role="user",
            metadata={"original": True},
        )

        copy = original.copy(model="gpt-4", metadata={"new": True})

        assert copy.audit_id == original.audit_id  # Not overridden
        assert copy.model == "gpt-4"  # Overridden
        assert copy.user_role == original.user_role  # Not overridden
        assert copy.metadata == {"original": True, "new": True}  # Merged

    def test_copy_metadata_merge(self):
        """Test that metadata is properly merged during copy."""
        original = Context(metadata={"a": 1, "b": 2})
        copy = original.copy(metadata={"b": 3, "c": 4})

        assert copy.metadata == {"a": 1, "b": 3, "c": 4}
        assert original.metadata == {"a": 1, "b": 2}  # Original unchanged

    def test_repr(self):
        """Test the string representation of Context."""
        ctx = Context(audit_id="test-audit", model="gpt-4", user_role="admin", purpose="test")

        repr_str = repr(ctx)
        assert "Context(" in repr_str
        assert "audit_id='test-audit'" in repr_str
        assert "model='gpt-4'" in repr_str
        assert "user_role='admin'" in repr_str
        assert "purpose='test'" in repr_str

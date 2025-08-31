"""Tests for the LengthGuard."""

from safellm.context import Context
from safellm.guards.length import LengthGuard


class TestLengthGuard:
    """Test the LengthGuard class."""

    def test_initialization_valid_params(self):
        """Test valid initialization parameters."""
        guard = LengthGuard(min_chars=10, max_chars=100, max_tokens=50)

        assert guard.name == "length"
        assert guard.min_chars == 10
        assert guard.max_chars == 100
        assert guard.max_tokens == 50

    def test_initialization_invalid_params(self):
        """Test invalid initialization parameters raise errors."""
        # Negative min_chars
        try:
            LengthGuard(min_chars=-1)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

        # Negative max_chars
        try:
            LengthGuard(max_chars=-1)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

        # min_chars > max_chars
        try:
            LengthGuard(min_chars=100, max_chars=50)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

    def test_check_valid_length(self):
        """Test checking valid length."""
        guard = LengthGuard(min_chars=5, max_chars=20)
        ctx = Context()

        decision = guard.check("Hello world", ctx)

        assert decision.allowed is True
        assert decision.action == "allow"
        assert decision.reasons == []
        assert decision.evidence["char_count"] == 11

    def test_check_too_short(self):
        """Test checking text that's too short."""
        guard = LengthGuard(min_chars=10)
        ctx = Context()

        decision = guard.check("Short", ctx)

        assert decision.allowed is False
        assert decision.action == "deny"
        assert len(decision.reasons) == 1
        assert "too short" in decision.reasons[0].lower()
        assert decision.evidence["char_count"] == 5

    def test_check_too_long(self):
        """Test checking text that's too long."""
        guard = LengthGuard(max_chars=5)
        ctx = Context()

        decision = guard.check("This text is too long", ctx)

        assert decision.allowed is False
        assert decision.action == "deny"
        assert len(decision.reasons) == 1
        assert "too long" in decision.reasons[0].lower()
        assert decision.evidence["char_count"] == 21

    def test_check_too_many_tokens(self):
        """Test checking text with too many tokens."""
        guard = LengthGuard(max_tokens=3)
        ctx = Context()

        decision = guard.check("This is a sentence with many tokens", ctx)

        assert decision.allowed is False
        assert decision.action == "deny"
        assert len(decision.reasons) == 1
        assert "too many tokens" in decision.reasons[0].lower()
        assert decision.evidence["token_count"] == 7

    def test_check_multiple_violations(self):
        """Test checking text with multiple violations."""
        guard = LengthGuard(min_chars=50, max_chars=100, max_tokens=2)
        ctx = Context()

        decision = guard.check("Short text with many words here", ctx)

        assert decision.allowed is False
        assert decision.action == "deny"
        assert len(decision.reasons) >= 2  # Should have multiple violations

    def test_check_non_string_data(self):
        """Test checking non-string data."""
        guard = LengthGuard(max_chars=5)
        ctx = Context()

        decision = guard.check(12345, ctx)

        assert decision.allowed is True  # "12345" has 5 chars, exactly at limit
        assert decision.evidence["char_count"] == 5

    def test_check_with_only_min_chars(self):
        """Test guard with only min_chars constraint."""
        guard = LengthGuard(min_chars=10)
        ctx = Context()

        # Valid case
        decision = guard.check("This is long enough", ctx)
        assert decision.allowed is True

        # Invalid case
        decision = guard.check("Short", ctx)
        assert decision.allowed is False

    def test_check_with_only_max_chars(self):
        """Test guard with only max_chars constraint."""
        guard = LengthGuard(max_chars=10)
        ctx = Context()

        # Valid case
        decision = guard.check("Short", ctx)
        assert decision.allowed is True

        # Invalid case
        decision = guard.check("This is way too long for the limit", ctx)
        assert decision.allowed is False

    def test_check_with_only_max_tokens(self):
        """Test guard with only max_tokens constraint."""
        guard = LengthGuard(max_tokens=3)
        ctx = Context()

        # Valid case
        decision = guard.check("Three words exactly", ctx)
        assert decision.allowed is True

        # Invalid case
        decision = guard.check("This has way too many words", ctx)
        assert decision.allowed is False

    def test_evidence_includes_token_count_when_relevant(self):
        """Test that evidence includes token_count only when max_tokens is set."""
        # With max_tokens
        guard_with_tokens = LengthGuard(max_tokens=5)
        ctx = Context()
        decision = guard_with_tokens.check("test text", ctx)
        assert "token_count" in decision.evidence

        # Without max_tokens
        guard_without_tokens = LengthGuard(max_chars=10)
        decision = guard_without_tokens.check("test text", ctx)
        assert "token_count" not in decision.evidence

"""Tests for the RateLimitGuard class."""

import time
import unittest

from safellm.context import Context
from safellm.guards.rate_limit import RateLimitGuard


class TestRateLimitGuard(unittest.TestCase):
    """Test the RateLimitGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = RateLimitGuard(max_requests=10, window_seconds=60)

        self.assertEqual(guard.name, "rate_limit")
        self.assertEqual(guard.max_requests, 10)
        self.assertEqual(guard.window_seconds, 60)

    def test_within_rate_limit(self):
        """Test requests within rate limit."""
        guard = RateLimitGuard(max_requests=5, window_seconds=60)
        ctx = Context()

        # First few requests should be allowed
        for i in range(3):
            result = guard.check(f"request {i}", ctx)
            self.assertEqual(result.action, "allow")

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded."""
        guard = RateLimitGuard(max_requests=2, window_seconds=60)
        ctx = Context()

        # First requests should be allowed
        result = guard.check("request 1", ctx)
        self.assertEqual(result.action, "allow")

        result = guard.check("request 2", ctx)
        self.assertEqual(result.action, "allow")

        # Third request should be denied
        result = guard.check("request 3", ctx)
        self.assertEqual(result.action, "deny")

    def test_time_window_reset(self):
        """Test time window reset."""
        guard = RateLimitGuard(max_requests=1, window_seconds=1)
        ctx = Context()

        # First request
        result = guard.check("request 1", ctx)
        self.assertEqual(result.action, "allow")

        # Wait for window to reset
        time.sleep(1.1)

        # Should be allowed again
        result = guard.check("request 2", ctx)
        self.assertEqual(result.action, "allow")

    def test_different_keys(self):
        """Test rate limiting with different keys."""
        guard = RateLimitGuard(max_requests=1, window_seconds=60)

        ctx1 = Context(user_role="user1")
        ctx2 = Context(user_role="user2")

        # Both should be allowed as they have different keys
        result1 = guard.check("request", ctx1)
        self.assertEqual(result1.action, "allow")

        result2 = guard.check("request", ctx2)
        self.assertEqual(result2.action, "allow")

    def test_zero_max_requests(self):
        """Test with zero max requests."""
        guard = RateLimitGuard(max_requests=0, window_seconds=60)
        ctx = Context()

        result = guard.check("request", ctx)
        self.assertEqual(result.action, "deny")


if __name__ == "__main__":
    unittest.main()

"""Rate limiting guard to prevent abuse and control usage."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard


class RateLimitGuard(BaseGuard):
    """Guard that enforces rate limiting based on user or session."""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 3600,  # 1 hour
        key_extractor: str = "user_role",  # Context field to use as key
        block_duration: int = 300,  # 5 minutes block
    ) -> None:
        """Initialize the rate limiting guard.
        
        Args:
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds
            key_extractor: Context field to use for rate limiting key
            block_duration: How long to block after limit exceeded (seconds)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_extractor = key_extractor
        self.block_duration = block_duration
        
        # In-memory storage (in production, use Redis or similar)
        self.request_history: dict[str, deque[float]] = defaultdict(deque)
        self.blocked_until: dict[str, float] = {}

    @property
    def name(self) -> str:
        return "rate_limit"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Check if the request is within rate limits."""
        # Extract rate limiting key from context
        rate_key = self._get_rate_key(ctx)
        current_time = time.time()
        
        # Check if currently blocked
        if rate_key in self.blocked_until:
            if current_time < self.blocked_until[rate_key]:
                remaining_time = int(self.blocked_until[rate_key] - current_time)
                return Decision.deny(
                    data,
                    [f"Rate limit exceeded. Blocked for {remaining_time} more seconds"],
                    audit_id=ctx.audit_id,
                    evidence={
                        "rate_key": rate_key,
                        "blocked_until": self.blocked_until[rate_key],
                        "remaining_seconds": remaining_time,
                    },
                )
            else:
                # Block period expired
                del self.blocked_until[rate_key]
        
        # Clean old requests outside the window
        request_times = self.request_history[rate_key]
        cutoff_time = current_time - self.window_seconds
        
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
        
        # Check if adding this request would exceed the limit
        if len(request_times) >= self.max_requests:
            # Block the user
            self.blocked_until[rate_key] = current_time + self.block_duration
            return Decision.deny(
                data,
                [f"Rate limit of {self.max_requests} requests per {self.window_seconds}s exceeded"],
                audit_id=ctx.audit_id,
                evidence={
                    "rate_key": rate_key,
                    "requests_in_window": len(request_times),
                    "max_requests": self.max_requests,
                    "window_seconds": self.window_seconds,
                    "blocked_for_seconds": self.block_duration,
                },
            )
        
        # Add current request to history
        request_times.append(current_time)
        
        return Decision.allow(
            data,
            audit_id=ctx.audit_id,
            evidence={
                "rate_key": rate_key,
                "requests_in_window": len(request_times),
                "requests_remaining": self.max_requests - len(request_times),
            },
        )

    def _get_rate_key(self, ctx: Context) -> str:
        """Extract rate limiting key from context."""
        if self.key_extractor == "audit_id":
            return ctx.audit_id
        elif self.key_extractor == "user_role":
            return ctx.user_role or "anonymous"
        elif self.key_extractor in ctx.metadata:
            return str(ctx.metadata[self.key_extractor])
        else:
            # Fallback to a generic key
            return "default"

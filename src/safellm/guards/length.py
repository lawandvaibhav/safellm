"""Length validation guard."""

from __future__ import annotations

from typing import Any

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard


class LengthGuard(BaseGuard):
    """Guard that validates the length of text content."""

    def __init__(
        self,
        *,
        min_chars: int | None = None,
        max_chars: int | None = None,
        max_tokens: int | None = None,
    ) -> None:
        """Initialize the length guard.

        Args:
            min_chars: Minimum number of characters (inclusive)
            max_chars: Maximum number of characters (inclusive)
            max_tokens: Maximum number of tokens (basic whitespace split)
        """
        if min_chars is not None and min_chars < 0:
            raise ValueError("min_chars must be non-negative")
        if max_chars is not None and max_chars < 0:
            raise ValueError("max_chars must be non-negative")
        if max_tokens is not None and max_tokens < 0:
            raise ValueError("max_tokens must be non-negative")
        if min_chars is not None and max_chars is not None and min_chars > max_chars:
            raise ValueError("min_chars cannot be greater than max_chars")

        self.min_chars = min_chars
        self.max_chars = max_chars
        self.max_tokens = max_tokens

    @property
    def name(self) -> str:
        return "length"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Check if the data meets length requirements."""
        # Convert data to string for length checking
        text = str(data) if not isinstance(data, str) else data

        char_count = len(text)
        token_count = len(text.split()) if self.max_tokens is not None else 0

        reasons: list[str] = []
        evidence: dict[str, Any] = {
            "char_count": char_count,
        }

        if self.max_tokens is not None:
            evidence["token_count"] = token_count

        # Check minimum characters
        if self.min_chars is not None and char_count < self.min_chars:
            reasons.append(f"Text too short: {char_count} < {self.min_chars} characters")

        # Check maximum characters
        if self.max_chars is not None and char_count > self.max_chars:
            reasons.append(f"Text too long: {char_count} > {self.max_chars} characters")

        # Check maximum tokens
        if self.max_tokens is not None and token_count > self.max_tokens:
            reasons.append(f"Too many tokens: {token_count} > {self.max_tokens} tokens")

        if reasons:
            return Decision.deny(
                data,
                reasons,
                audit_id=ctx.audit_id,
                evidence=evidence,
            )

        return Decision.allow(
            data,
            audit_id=ctx.audit_id,
            evidence=evidence,
        )

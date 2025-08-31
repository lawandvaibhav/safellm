"""Decision types and validation errors for SafeLLM."""

from __future__ import annotations

import uuid
from typing import Any, Literal, NamedTuple


class Decision(NamedTuple):
    """Result of a validation pipeline or guard check.
    
    Attributes:
        allowed: Whether the data passed validation
        action: The action to take (allow, deny, transform, retry)
        reasons: List of human-readable reasons for the decision
        evidence: Dictionary containing evidence for the decision (offending spans, rule IDs, etc.)
        output: The original or transformed data
        audit_id: Unique identifier for correlating with logs and traces
    """
    allowed: bool
    action: Literal["allow", "deny", "transform", "retry"]
    reasons: list[str]
    evidence: dict[str, Any]
    output: Any
    audit_id: str

    @classmethod
    def allow(
        cls,
        output: Any,
        *,
        audit_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> Decision:
        """Create an allow decision."""
        return cls(
            allowed=True,
            action="allow",
            reasons=[],
            evidence=evidence or {},
            output=output,
            audit_id=audit_id or str(uuid.uuid4()),
        )

    @classmethod
    def deny(
        cls,
        output: Any,
        reasons: list[str],
        *,
        audit_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> Decision:
        """Create a deny decision."""
        return cls(
            allowed=False,
            action="deny",
            reasons=reasons,
            evidence=evidence or {},
            output=output,
            audit_id=audit_id or str(uuid.uuid4()),
        )

    @classmethod
    def transform(
        cls,
        original: Any,
        transformed: Any,
        reasons: list[str],
        *,
        audit_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> Decision:
        """Create a transform decision."""
        return cls(
            allowed=True,
            action="transform",
            reasons=reasons,
            evidence=evidence or {},
            output=transformed,
            audit_id=audit_id or str(uuid.uuid4()),
        )

    @classmethod
    def retry(
        cls,
        output: Any,
        reasons: list[str],
        *,
        audit_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> Decision:
        """Create a retry decision."""
        return cls(
            allowed=False,
            action="retry",
            reasons=reasons,
            evidence=evidence or {},
            output=output,
            audit_id=audit_id or str(uuid.uuid4()),
        )


class ValidationError(Exception):
    """Exception raised when validation fails."""

    def __init__(self, decision: Decision) -> None:
        self.decision = decision
        super().__init__("; ".join(decision.reasons))

    @property
    def audit_id(self) -> str:
        """Get the audit ID from the decision."""
        return self.decision.audit_id

    @property
    def reasons(self) -> list[str]:
        """Get the reasons from the decision."""
        return self.decision.reasons

    @property
    def evidence(self) -> dict[str, Any]:
        """Get the evidence from the decision."""
        return self.decision.evidence

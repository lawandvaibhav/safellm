"""Context object for validation pipeline."""

from __future__ import annotations

import uuid
from typing import Any


class Context:
    """Context object that holds metadata for validation requests.
    
    This object is passed between guards and can hold request-specific
    information like model type, user role, purpose, trace IDs, and random seeds.
    """

    def __init__(
        self,
        *,
        audit_id: str | None = None,
        model: str | None = None,
        user_role: str | None = None,
        purpose: str | None = None,
        trace_id: str | None = None,
        seed: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize context.
        
        Args:
            audit_id: Unique identifier for this validation request
            model: Name/identifier of the LLM model being used
            user_role: Role of the user making the request
            purpose: Purpose/intent of the request
            trace_id: Distributed tracing identifier
            seed: Random seed for reproducible results
            metadata: Additional arbitrary metadata
        """
        self.audit_id = audit_id or str(uuid.uuid4())
        self.model = model
        self.user_role = user_role
        self.purpose = purpose
        self.trace_id = trace_id
        self.seed = seed
        self.metadata = metadata or {}

    def copy(self, **overrides: Any) -> Context:
        """Create a copy of this context with optional overrides."""
        return Context(
            audit_id=overrides.get("audit_id", self.audit_id),
            model=overrides.get("model", self.model),
            user_role=overrides.get("user_role", self.user_role),
            purpose=overrides.get("purpose", self.purpose),
            trace_id=overrides.get("trace_id", self.trace_id),
            seed=overrides.get("seed", self.seed),
            metadata={**self.metadata, **overrides.get("metadata", {})},
        )

    def __repr__(self) -> str:
        return (
            f"Context(audit_id={self.audit_id!r}, model={self.model!r}, "
            f"user_role={self.user_role!r}, purpose={self.purpose!r})"
        )

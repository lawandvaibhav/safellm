"""Validation pipeline for SafeLLM."""

from __future__ import annotations

import logging
from typing import Any, Literal, Sequence

from .context import Context
from .decisions import Decision
from .guard import Guard

logger = logging.getLogger(__name__)


class Pipeline:
    """Validation pipeline that executes a sequence of guards.
    
    The pipeline runs guards in order and can be configured to fail fast
    or continue on errors.
    """

    def __init__(
        self,
        name: str,
        steps: Sequence[Guard],
        *,
        fail_fast: bool = True,
        on_error: Literal["deny", "allow", "transform"] = "deny",
    ) -> None:
        """Initialize the pipeline.
        
        Args:
            name: Name of the pipeline for identification
            steps: Sequence of guards to execute in order
            fail_fast: Whether to stop on the first failure
            on_error: Default action when a guard raises an exception
        """
        self.name = name
        self.steps = list(steps)
        self.fail_fast = fail_fast
        self.on_error = on_error

        if not self.steps:
            raise ValueError("Pipeline must have at least one guard")

    def validate(self, data: Any, *, ctx: Context | None = None) -> Decision:
        """Synchronously validate data through the pipeline.
        
        Args:
            data: The data to validate
            ctx: Optional context object (will be created if not provided)
            
        Returns:
            Final decision from the pipeline
        """
        if ctx is None:
            ctx = Context()

        current_data = data
        all_reasons: list[str] = []
        all_evidence: dict[str, Any] = {}
        transformations = 0

        logger.debug(f"Starting pipeline {self.name} validation", extra={"audit_id": ctx.audit_id})

        for i, guard in enumerate(self.steps):
            try:
                logger.debug(
                    f"Running guard {guard.name} (step {i+1}/{len(self.steps)})",
                    extra={"audit_id": ctx.audit_id, "guard": guard.name}
                )
                
                decision = guard.check(current_data, ctx)
                
                # Collect reasons and evidence
                all_reasons.extend(decision.reasons)
                all_evidence.update(decision.evidence)

                if decision.action == "deny":
                    logger.info(
                        f"Guard {guard.name} denied request: {', '.join(decision.reasons)}",
                        extra={"audit_id": ctx.audit_id, "guard": guard.name}
                    )
                    if self.fail_fast:
                        return Decision.deny(
                            current_data,
                            all_reasons,
                            audit_id=ctx.audit_id,
                            evidence=all_evidence,
                        )
                
                elif decision.action == "transform":
                    logger.debug(
                        f"Guard {guard.name} transformed data: {', '.join(decision.reasons)}",
                        extra={"audit_id": ctx.audit_id, "guard": guard.name}
                    )
                    current_data = decision.output
                    transformations += 1
                
                elif decision.action == "retry":
                    logger.info(
                        f"Guard {guard.name} requested retry: {', '.join(decision.reasons)}",
                        extra={"audit_id": ctx.audit_id, "guard": guard.name}
                    )
                    if self.fail_fast:
                        return Decision.retry(
                            current_data,
                            all_reasons,
                            audit_id=ctx.audit_id,
                            evidence=all_evidence,
                        )

            except Exception as e:
                logger.error(
                    f"Guard {guard.name} raised exception: {e}",
                    extra={"audit_id": ctx.audit_id, "guard": guard.name},
                    exc_info=True
                )
                
                error_reason = f"Guard {guard.name} failed: {str(e)}"
                all_reasons.append(error_reason)
                
                if self.on_error == "deny" or self.fail_fast:
                    return Decision.deny(
                        current_data,
                        all_reasons,
                        audit_id=ctx.audit_id,
                        evidence=all_evidence,
                    )
                elif self.on_error == "allow":
                    # Continue with original data
                    continue
                # For "transform", we also continue

        # If we get here, all guards passed or we're not failing fast
        if all_reasons:
            # Some guards had issues but we continued
            if transformations > 0:
                return Decision.transform(
                    data,
                    current_data,
                    all_reasons,
                    audit_id=ctx.audit_id,
                    evidence=all_evidence,
                )
            else:
                # Had issues but no transformations
                return Decision.allow(
                    current_data,
                    audit_id=ctx.audit_id,
                    evidence=all_evidence,
                )
        else:
            # Clean run
            if transformations > 0:
                return Decision.transform(
                    data,
                    current_data,
                    [f"Applied {transformations} transformation(s)"],
                    audit_id=ctx.audit_id,
                    evidence=all_evidence,
                )
            else:
                return Decision.allow(
                    current_data,
                    audit_id=ctx.audit_id,
                    evidence=all_evidence,
                )

    async def avalidate(self, data: Any, *, ctx: Context | None = None) -> Decision:
        """Asynchronously validate data through the pipeline.
        
        Args:
            data: The data to validate
            ctx: Optional context object (will be created if not provided)
            
        Returns:
            Final decision from the pipeline
        """
        if ctx is None:
            ctx = Context()

        current_data = data
        all_reasons: list[str] = []
        all_evidence: dict[str, Any] = {}
        transformations = 0

        logger.debug(f"Starting async pipeline {self.name} validation", extra={"audit_id": ctx.audit_id})

        for i, guard in enumerate(self.steps):
            try:
                logger.debug(
                    f"Running guard {guard.name} (step {i+1}/{len(self.steps)})",
                    extra={"audit_id": ctx.audit_id, "guard": guard.name}
                )
                
                decision = await guard.acheck(current_data, ctx)
                
                # Collect reasons and evidence
                all_reasons.extend(decision.reasons)
                all_evidence.update(decision.evidence)

                if decision.action == "deny":
                    logger.info(
                        f"Guard {guard.name} denied request: {', '.join(decision.reasons)}",
                        extra={"audit_id": ctx.audit_id, "guard": guard.name}
                    )
                    if self.fail_fast:
                        return Decision.deny(
                            current_data,
                            all_reasons,
                            audit_id=ctx.audit_id,
                            evidence=all_evidence,
                        )
                
                elif decision.action == "transform":
                    logger.debug(
                        f"Guard {guard.name} transformed data: {', '.join(decision.reasons)}",
                        extra={"audit_id": ctx.audit_id, "guard": guard.name}
                    )
                    current_data = decision.output
                    transformations += 1
                
                elif decision.action == "retry":
                    logger.info(
                        f"Guard {guard.name} requested retry: {', '.join(decision.reasons)}",
                        extra={"audit_id": ctx.audit_id, "guard": guard.name}
                    )
                    if self.fail_fast:
                        return Decision.retry(
                            current_data,
                            all_reasons,
                            audit_id=ctx.audit_id,
                            evidence=all_evidence,
                        )

            except Exception as e:
                logger.error(
                    f"Guard {guard.name} raised exception: {e}",
                    extra={"audit_id": ctx.audit_id, "guard": guard.name},
                    exc_info=True
                )
                
                error_reason = f"Guard {guard.name} failed: {str(e)}"
                all_reasons.append(error_reason)
                
                if self.on_error == "deny" or self.fail_fast:
                    return Decision.deny(
                        current_data,
                        all_reasons,
                        audit_id=ctx.audit_id,
                        evidence=all_evidence,
                    )
                elif self.on_error == "allow":
                    # Continue with original data
                    continue
                # For "transform", we also continue

        # If we get here, all guards passed or we're not failing fast
        if all_reasons:
            # Some guards had issues but we continued
            if transformations > 0:
                return Decision.transform(
                    data,
                    current_data,
                    all_reasons,
                    audit_id=ctx.audit_id,
                    evidence=all_evidence,
                )
            else:
                # Had issues but no transformations
                return Decision.allow(
                    current_data,
                    audit_id=ctx.audit_id,
                    evidence=all_evidence,
                )
        else:
            # Clean run
            if transformations > 0:
                return Decision.transform(
                    data,
                    current_data,
                    [f"Applied {transformations} transformation(s)"],
                    audit_id=ctx.audit_id,
                    evidence=all_evidence,
                )
            else:
                return Decision.allow(
                    current_data,
                    audit_id=ctx.audit_id,
                    evidence=all_evidence,
                )

    def __repr__(self) -> str:
        return f"Pipeline(name={self.name!r}, steps={len(self.steps)}, fail_fast={self.fail_fast})"

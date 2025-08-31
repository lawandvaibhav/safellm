"""Business rules guard for domain-specific validation."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard


class BusinessRulesGuard(BaseGuard):
    """Guard that enforces custom business rules and domain logic."""

    def __init__(
        self,
        rules: list[dict[str, Any]],
        action: Literal["block", "flag", "transform"] = "block",
        require_all: bool = False,
    ) -> None:
        """Initialize the business rules guard.

        Args:
            rules: List of business rule definitions
            action: What to do when rules are violated
            require_all: Whether all rules must pass (True) or any rule (False)
        """
        self.action = action
        self.require_all = require_all
        self.rules = self._parse_rules(rules)

    @property
    def name(self) -> str:
        return "business_rules"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Check data against business rules."""
        rule_results = []
        passed_rules = []
        failed_rules = []

        for rule in self.rules:
            try:
                result = self._evaluate_rule(rule, data, ctx)
                rule_results.append(
                    {
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "passed": result["passed"],
                        "value": result.get("value"),
                        "message": result.get("message"),
                        "details": result.get("details", {}),
                    }
                )

                if result["passed"]:
                    passed_rules.append(rule["id"])
                else:
                    failed_rules.append(rule["id"])

            except Exception as e:
                rule_results.append(
                    {
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "passed": False,
                        "error": str(e),
                        "exception_type": type(e).__name__,
                    }
                )
                failed_rules.append(rule["id"])

        # Determine overall result
        if self.require_all:
            overall_passed = len(failed_rules) == 0
        else:
            overall_passed = len(passed_rules) > 0

        evidence = {
            "rules_evaluated": len(self.rules),
            "rules_passed": len(passed_rules),
            "rules_failed": len(failed_rules),
            "require_all_rules": self.require_all,
            "overall_passed": overall_passed,
            "rule_results": rule_results,
            "passed_rule_ids": passed_rules,
            "failed_rule_ids": failed_rules,
        }

        if not overall_passed:
            failed_rule_names = [r["rule_name"] for r in rule_results if not r["passed"]]
            reasons = [f"Business rule violation: {len(failed_rules)} rule(s) failed"]
            reasons.extend(
                [f"Failed: {name}" for name in failed_rule_names[:3]]
            )  # Limit to first 3

            if len(failed_rule_names) > 3:
                reasons.append(f"... and {len(failed_rule_names) - 3} more")

            if self.action == "block":
                return Decision.deny(
                    data,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            elif self.action == "transform":
                transformed_data = self._apply_transformations(data, rule_results)
                if transformed_data != data:
                    reasons.append("Applied business rule transformations")
                    evidence["transformed"] = True
                    return Decision.transform(
                        data,
                        transformed_data,
                        reasons,
                        audit_id=ctx.audit_id,
                        evidence=evidence,
                    )
                else:
                    # No transformations available, treat as block
                    return Decision.deny(
                        data,
                        reasons + ["No transformations available"],
                        audit_id=ctx.audit_id,
                        evidence=evidence,
                    )
            else:  # flag
                return Decision.allow(
                    data,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )

        return Decision.allow(
            data,
            audit_id=ctx.audit_id,
            evidence=evidence,
        )

    def _parse_rules(self, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse and validate rule definitions."""
        parsed_rules = []

        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise ValueError(f"Rule {i} must be a dictionary")

            rule_id = rule.get("id", f"rule_{i}")
            rule_name = rule.get("name", rule_id)
            rule_type = rule.get("type", "custom")

            parsed_rule = {
                "id": rule_id,
                "name": rule_name,
                "type": rule_type,
                "description": rule.get("description", ""),
                "config": rule.get("config", {}),
            }

            # Validate rule type and configuration
            if rule_type == "range":
                self._validate_range_rule(parsed_rule)
            elif rule_type == "pattern":
                self._validate_pattern_rule(parsed_rule)
            elif rule_type == "length":
                self._validate_length_rule(parsed_rule)
            elif rule_type == "time_window":
                self._validate_time_window_rule(parsed_rule)
            elif rule_type == "value_list":
                self._validate_value_list_rule(parsed_rule)
            elif rule_type == "custom":
                self._validate_custom_rule(parsed_rule, rule)
            else:
                raise ValueError(f"Unknown rule type: {rule_type}")

            parsed_rules.append(parsed_rule)

        return parsed_rules

    def _validate_range_rule(self, rule: dict[str, Any]) -> None:
        """Validate range rule configuration."""
        config = rule["config"]
        if "min" not in config and "max" not in config:
            raise ValueError(f"Range rule '{rule['id']}' must specify min and/or max")

    def _validate_pattern_rule(self, rule: dict[str, Any]) -> None:
        """Validate pattern rule configuration."""
        config = rule["config"]
        if "pattern" not in config:
            raise ValueError(f"Pattern rule '{rule['id']}' must specify pattern")

        try:
            re.compile(config["pattern"])
        except re.error as e:
            raise ValueError(f"Invalid regex pattern in rule '{rule['id']}': {e}") from e

    def _validate_length_rule(self, rule: dict[str, Any]) -> None:
        """Validate length rule configuration."""
        config = rule["config"]
        if "min_length" not in config and "max_length" not in config:
            raise ValueError(
                f"Length rule '{rule['id']}' must specify min_length and/or max_length"
            )

    def _validate_time_window_rule(self, rule: dict[str, Any]) -> None:
        """Validate time window rule configuration."""
        config = rule["config"]
        if "start_time" not in config or "end_time" not in config:
            raise ValueError(
                f"Time window rule '{rule['id']}' must specify start_time and end_time"
            )

    def _validate_value_list_rule(self, rule: dict[str, Any]) -> None:
        """Validate value list rule configuration."""
        config = rule["config"]
        if "allowed_values" not in config and "forbidden_values" not in config:
            raise ValueError(
                f"Value list rule '{rule['id']}' must specify allowed_values or forbidden_values"
            )

    def _validate_custom_rule(self, rule: dict[str, Any], original_rule: dict[str, Any]) -> None:
        """Validate custom rule configuration."""
        if "validator" not in original_rule:
            raise ValueError(f"Custom rule '{rule['id']}' must specify validator function")

        if not callable(original_rule["validator"]):
            raise ValueError(f"Custom rule '{rule['id']}' validator must be callable")

        rule["validator"] = original_rule["validator"]

    def _evaluate_rule(self, rule: dict[str, Any], data: Any, ctx: Context) -> dict[str, Any]:
        """Evaluate a single business rule."""
        rule_type = rule["type"]
        config = rule["config"]

        if rule_type == "range":
            return self._evaluate_range_rule(config, data)
        elif rule_type == "pattern":
            return self._evaluate_pattern_rule(config, data)
        elif rule_type == "length":
            return self._evaluate_length_rule(config, data)
        elif rule_type == "time_window":
            return self._evaluate_time_window_rule(config, data, ctx)
        elif rule_type == "value_list":
            return self._evaluate_value_list_rule(config, data)
        elif rule_type == "custom":
            return self._evaluate_custom_rule(rule, data, ctx)
        else:
            return {"passed": False, "message": f"Unknown rule type: {rule_type}"}

    def _evaluate_range_rule(self, config: dict[str, Any], data: Any) -> dict[str, Any]:
        """Evaluate range rule."""
        try:
            value = float(data) if isinstance(data, (int, float, str)) else None
            if value is None:
                return {"passed": False, "message": "Value cannot be converted to number"}

            min_val = config.get("min")
            max_val = config.get("max")

            if min_val is not None and value < min_val:
                return {
                    "passed": False,
                    "value": value,
                    "message": f"Value {value} is below minimum {min_val}",
                    "details": {"min_value": min_val, "actual_value": value},
                }

            if max_val is not None and value > max_val:
                return {
                    "passed": False,
                    "value": value,
                    "message": f"Value {value} exceeds maximum {max_val}",
                    "details": {"max_value": max_val, "actual_value": value},
                }

            return {
                "passed": True,
                "value": value,
                "message": f"Value {value} is within range",
                "details": {"min_value": min_val, "max_value": max_val, "actual_value": value},
            }

        except (ValueError, TypeError) as e:
            return {"passed": False, "message": f"Range evaluation error: {e}"}

    def _evaluate_pattern_rule(self, config: dict[str, Any], data: Any) -> dict[str, Any]:
        """Evaluate pattern rule."""
        text = str(data)
        pattern = config["pattern"]
        match_required = config.get("match_required", True)

        try:
            match = re.search(pattern, text)
            if match_required:
                passed = bool(match)
                message = "Pattern matched" if passed else "Pattern not found"
            else:
                passed = not bool(match)
                message = "Pattern not found" if passed else "Forbidden pattern found"

            details = {
                "pattern": pattern,
                "match_required": match_required,
                "text_length": len(text),
            }

            if match:
                details.update(
                    {
                        "match_text": match.group(),
                        "match_start": match.start(),
                        "match_end": match.end(),
                    }
                )

            return {
                "passed": passed,
                "message": message,
                "details": details,
            }

        except re.error as e:
            return {"passed": False, "message": f"Pattern error: {e}"}

    def _evaluate_length_rule(self, config: dict[str, Any], data: Any) -> dict[str, Any]:
        """Evaluate length rule."""
        text = str(data)
        length = len(text)

        min_length = config.get("min_length")
        max_length = config.get("max_length")

        if min_length is not None and length < min_length:
            return {
                "passed": False,
                "message": f"Length {length} is below minimum {min_length}",
                "details": {"min_length": min_length, "actual_length": length},
            }

        if max_length is not None and length > max_length:
            return {
                "passed": False,
                "message": f"Length {length} exceeds maximum {max_length}",
                "details": {"max_length": max_length, "actual_length": length},
            }

        return {
            "passed": True,
            "message": f"Length {length} is within bounds",
            "details": {
                "min_length": min_length,
                "max_length": max_length,
                "actual_length": length,
            },
        }

    def _evaluate_time_window_rule(
        self, config: dict[str, Any], data: Any, ctx: Context
    ) -> dict[str, Any]:
        """Evaluate time window rule."""
        from datetime import datetime
        current_time = datetime.utcnow()

        start_time = config["start_time"]
        end_time = config["end_time"]

        # Parse time strings if needed
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        in_window = start_time <= current_time <= end_time

        return {
            "passed": in_window,
            "message": f"Current time {'is' if in_window else 'is not'} within allowed window",
            "details": {
                "current_time": current_time.isoformat(),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "in_window": in_window,
            },
        }

    def _evaluate_value_list_rule(self, config: dict[str, Any], data: Any) -> dict[str, Any]:
        """Evaluate value list rule."""
        value = str(data)

        allowed_values = config.get("allowed_values")
        forbidden_values = config.get("forbidden_values")
        case_sensitive = config.get("case_sensitive", True)

        if not case_sensitive:
            value = value.lower()
            if allowed_values:
                allowed_values = [v.lower() for v in allowed_values]
            if forbidden_values:
                forbidden_values = [v.lower() for v in forbidden_values]

        details = {
            "value": value,
            "case_sensitive": case_sensitive,
        }

        if allowed_values is not None:
            passed = value in allowed_values
            details["allowed_values"] = allowed_values
            message = f"Value {'is' if passed else 'is not'} in allowed list"
        elif forbidden_values is not None:
            passed = value not in forbidden_values
            details["forbidden_values"] = forbidden_values
            message = f"Value {'is not' if passed else 'is'} in forbidden list"
        else:
            passed = True
            message = "No value restrictions"

        return {
            "passed": passed,
            "message": message,
            "details": details,
        }

    def _evaluate_custom_rule(
        self, rule: dict[str, Any], data: Any, ctx: Context
    ) -> dict[str, Any]:
        """Evaluate custom rule."""
        try:
            validator = rule["validator"]
            result = validator(data, ctx, rule["config"])

            # Ensure result is in expected format
            if isinstance(result, bool):
                return {
                    "passed": result,
                    "message": f"Custom rule {'passed' if result else 'failed'}",
                }
            elif isinstance(result, dict):
                if "passed" not in result:
                    result["passed"] = False
                if "message" not in result:
                    result["message"] = f"Custom rule {'passed' if result['passed'] else 'failed'}"
                return result
            else:
                return {
                    "passed": False,
                    "message": f"Invalid custom rule result type: {type(result)}",
                }

        except Exception as e:
            return {
                "passed": False,
                "message": f"Custom rule error: {e}",
                "exception_type": type(e).__name__,
            }

    def _apply_transformations(self, data: Any, rule_results: list[dict[str, Any]]) -> Any:
        """Apply transformations based on rule results."""
        # This is a placeholder for transformation logic
        # In practice, you would implement specific transformations
        # based on failed rules and their configurations

        transformed_data = data

        for result in rule_results:
            if not result["passed"] and "transformation" in result:
                # Apply transformation if specified
                transformation = result["transformation"]
                if callable(transformation):
                    transformed_data = transformation(transformed_data)

        return transformed_data

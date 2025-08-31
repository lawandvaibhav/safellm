"""Format validation guard for structured data validation."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard


class FormatGuard(BaseGuard):
    """Guard that validates data against expected formats."""

    def __init__(
        self,
        format_type: Literal["json", "email", "url", "phone", "credit_card", "ipv4", "ipv6", "uuid", "custom"],
        pattern: str | None = None,
        action: Literal["block", "flag", "transform"] = "block",
        strict: bool = True,
        allow_null: bool = False,
    ) -> None:
        """Initialize the format guard.

        Args:
            format_type: Type of format to validate against
            pattern: Custom regex pattern for 'custom' format_type
            action: What to do when validation fails
            strict: Whether to use strict validation
            allow_null: Whether to allow null/empty values
        """
        self.format_type = format_type
        self.action = action
        self.strict = strict
        self.allow_null = allow_null

        if format_type == "custom" and not pattern:
            raise ValueError("Custom format requires a pattern")

        self.pattern = pattern
        self._compiled_pattern = None

        if format_type == "custom" and pattern:
            self._compiled_pattern = re.compile(pattern)

    @property
    def name(self) -> str:
        return f"format_{self.format_type}"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Validate data against the specified format."""
        # Handle null/empty values
        if data is None or data == "":
            if self.allow_null:
                return Decision.allow(
                    data,
                    audit_id=ctx.audit_id,
                    evidence={"format_type": self.format_type, "allowed_null": True},
                )
            else:
                return Decision.deny(
                    data,
                    [f"Null/empty value not allowed for format: {self.format_type}"],
                    audit_id=ctx.audit_id,
                    evidence={"format_type": self.format_type, "error": "null_value"},
                )

        # Convert to string for pattern matching
        if not isinstance(data, str):
            text = str(data)
        else:
            text = data

        # Validate format
        is_valid, error_details = self._validate_format(text)

        evidence = {
            "format_type": self.format_type,
            "strict_mode": self.strict,
            "input_length": len(text),
            "validation_result": is_valid,
        }

        if error_details:
            evidence.update(error_details)

        if not is_valid:
            reasons = [f"Invalid format: expected {self.format_type}"]
            if error_details.get("error"):
                reasons.append(f"Error: {error_details['error']}")

            if self.action == "block":
                return Decision.deny(
                    data,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            elif self.action == "transform":
                transformed = self._attempt_transform(text)
                if transformed != text:
                    reasons.append("Data transformed to valid format")
                    evidence["transformed"] = True
                    return Decision.transform(
                        data,
                        transformed,
                        reasons,
                        audit_id=ctx.audit_id,
                        evidence=evidence,
                    )
                else:
                    # Can't transform, treat as block
                    return Decision.deny(
                        data,
                        reasons + ["Could not transform to valid format"],
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

    def _validate_format(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate text against the specified format."""
        error_details = {}

        try:
            if self.format_type == "json":
                return self._validate_json(text)
            elif self.format_type == "email":
                return self._validate_email(text)
            elif self.format_type == "url":
                return self._validate_url(text)
            elif self.format_type == "phone":
                return self._validate_phone(text)
            elif self.format_type == "credit_card":
                return self._validate_credit_card(text)
            elif self.format_type == "ipv4":
                return self._validate_ipv4(text)
            elif self.format_type == "ipv6":
                return self._validate_ipv6(text)
            elif self.format_type == "uuid":
                return self._validate_uuid(text)
            elif self.format_type == "custom":
                return self._validate_custom(text)
            else:
                error_details["error"] = f"Unknown format type: {self.format_type}"
                return False, error_details

        except Exception as e:
            error_details["error"] = str(e)
            error_details["exception_type"] = type(e).__name__
            return False, error_details

    def _validate_json(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate JSON format."""
        try:
            parsed = json.loads(text)
            return True, {"parsed_type": type(parsed).__name__}
        except json.JSONDecodeError as e:
            return False, {
                "error": f"Invalid JSON: {e.msg}",
                "position": e.pos,
                "line": e.lineno,
                "column": e.colno,
            }

    def _validate_email(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate email format."""
        if self.strict:
            # RFC 5322 compliant pattern (simplified)
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        else:
            # Basic email pattern
            pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'

        is_valid = bool(re.match(pattern, text))
        details = {"strict_mode": self.strict}

        if is_valid:
            parts = text.split('@')
            details.update({
                "local_part": parts[0],
                "domain": parts[1],
            })
        else:
            details["error"] = "Invalid email format"

        return is_valid, details

    def _validate_url(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate URL format."""
        if self.strict:
            # Strict URL pattern with protocol
            pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        else:
            # Basic URL pattern
            pattern = r'^https?://\S+$'

        is_valid = bool(re.match(pattern, text))
        details = {"strict_mode": self.strict}

        if is_valid:
            # Extract URL components
            match = re.match(r'^(https?)://([^:/]+)(?::(\d+))?(/.*)?$', text)
            if match:
                details.update({
                    "scheme": match.group(1),
                    "host": match.group(2),
                    "port": match.group(3),
                    "path": match.group(4) or "/",
                })
        else:
            details["error"] = "Invalid URL format"

        return is_valid, details

    def _validate_phone(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate phone number format."""
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\.]', '', text)

        if self.strict:
            # E.164 format: +1234567890
            pattern = r'^\+\d{1,3}\d{4,14}$'
        else:
            # US format or international
            pattern = r'^(?:\+?1)?[2-9]\d{2}[2-9]\d{2}\d{4}$|^\+\d{1,3}\d{4,14}$'

        is_valid = bool(re.match(pattern, cleaned))
        details = {
            "strict_mode": self.strict,
            "cleaned_number": cleaned,
            "original_format": text,
        }

        if not is_valid:
            details["error"] = "Invalid phone number format"

        return is_valid, details

    def _validate_credit_card(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate credit card format."""
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s\-]', '', text)

        # Basic pattern: 13-19 digits
        if not re.match(r'^\d{13,19}$', cleaned):
            return False, {"error": "Invalid credit card format: must be 13-19 digits"}

        # Luhn algorithm check if strict
        if self.strict:
            is_valid = self._luhn_check(cleaned)
            if not is_valid:
                return False, {"error": "Invalid credit card: failed Luhn check"}

        # Detect card type
        card_type = self._detect_card_type(cleaned)

        return True, {
            "cleaned_number": cleaned,
            "card_type": card_type,
            "luhn_valid": self.strict and self._luhn_check(cleaned),
        }

    def _validate_ipv4(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate IPv4 address format."""
        pattern = r'^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$'
        is_valid = bool(re.match(pattern, text))

        details = {}
        if is_valid:
            octets = [int(octet) for octet in text.split('.')]
            details["octets"] = octets
            details["is_private"] = self._is_private_ipv4(octets)
        else:
            details["error"] = "Invalid IPv4 address format"

        return is_valid, details

    def _validate_ipv6(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate IPv6 address format."""
        # Simplified IPv6 validation
        pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$'
        compressed_pattern = r'^(?:[0-9a-fA-F]{1,4}:)*::(?:[0-9a-fA-F]{1,4}:)*[0-9a-fA-F]{1,4}$'

        is_valid = bool(re.match(pattern, text) or re.match(compressed_pattern, text))

        details = {}
        if is_valid:
            details["compressed"] = "::" in text
        else:
            details["error"] = "Invalid IPv6 address format"

        return is_valid, details

    def _validate_uuid(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate UUID format."""
        pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        is_valid = bool(re.match(pattern, text))

        details = {}
        if is_valid:
            # Extract version
            version = int(text[14], 16) >> 2
            details["version"] = version
        else:
            details["error"] = "Invalid UUID format"

        return is_valid, details

    def _validate_custom(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Validate against custom pattern."""
        if not self._compiled_pattern:
            return False, {"error": "No custom pattern defined"}

        match = self._compiled_pattern.match(text)
        is_valid = bool(match)

        details = {"pattern": self.pattern}
        if match and match.groups():
            details["groups"] = match.groups()
        if not is_valid:
            details["error"] = "Text does not match custom pattern"

        return is_valid, details

    def _attempt_transform(self, text: str) -> str:
        """Attempt to transform data to valid format."""
        if self.format_type == "email":
            # Remove whitespace and convert to lowercase
            return text.strip().lower()
        elif self.format_type == "url":
            # Add http:// if missing
            if not text.startswith(('http://', 'https://')):
                return f"http://{text}"
        elif self.format_type == "phone":
            # Clean phone number format
            cleaned = re.sub(r'[\s\-\(\)\.]', '', text)
            if cleaned.startswith('1') and len(cleaned) == 11:
                return f"+{cleaned}"
            elif len(cleaned) == 10:
                return f"+1{cleaned}"
        elif self.format_type == "credit_card":
            # Remove spaces and dashes
            return re.sub(r'[\s\-]', '', text)

        return text

    def _luhn_check(self, number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        total = 0
        reverse_digits = number[::-1]

        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n = (n // 10) + (n % 10)
            total += n

        return total % 10 == 0

    def _detect_card_type(self, number: str) -> str:
        """Detect credit card type from number."""
        if number.startswith('4'):
            return 'Visa'
        elif number.startswith('5') or number.startswith('2'):
            return 'Mastercard'
        elif number.startswith('3'):
            return 'American Express'
        elif number.startswith('6'):
            return 'Discover'
        else:
            return 'Unknown'

    def _is_private_ipv4(self, octets: list[int]) -> bool:
        """Check if IPv4 address is in private range."""
        # 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
        return (
            octets[0] == 10 or
            (octets[0] == 172 and 16 <= octets[1] <= 31) or
            (octets[0] == 192 and octets[1] == 168)
        )

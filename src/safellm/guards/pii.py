"""PII detection and redaction guard."""

from __future__ import annotations

from re import Pattern
from typing import Any, Literal

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard
from ..utils.patterns import (
    ADDRESS_PATTERNS,
    CREDIT_CARD_PATTERNS,
    EMAIL_PATTERN,
    IBAN_PATTERN,
    IPV4_PATTERN,
    IPV6_PATTERN,
    PHONE_PATTERNS,
    SSN_PATTERN,
    luhn_check,
    mask_credit_card,
    mask_email,
    mask_phone,
    mask_text,
)


class PiiRedactionGuard(BaseGuard):
    """Guard that detects and redacts personally identifiable information (PII)."""

    # Default PII types to detect
    DEFAULT_TARGETS = [
        "email",
        "phone",
        "credit_card",
        "ssn",
        "ip_address",
        "iban",
    ]

    def __init__(
        self,
        mode: Literal["mask", "remove"] = "mask",
        targets: list[str] | None = None,
        custom_patterns: list[Pattern[str]] | None = None,
    ) -> None:
        """Initialize the PII redaction guard.

        Args:
            mode: How to handle detected PII - 'mask' or 'remove'
            targets: List of PII types to detect (default: all supported types)
            custom_patterns: Additional regex patterns to check
        """
        self.mode = mode
        self.targets = targets or self.DEFAULT_TARGETS
        self.custom_patterns = custom_patterns or []

        # Validate targets
        supported_targets = {
            "email",
            "phone",
            "credit_card",
            "ssn",
            "ip_address",
            "iban",
            "address",
        }
        invalid_targets = set(self.targets) - supported_targets
        if invalid_targets:
            raise ValueError(f"Unsupported PII targets: {invalid_targets}")

    @property
    def name(self) -> str:
        return "pii_redaction"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Detect and redact PII in the data."""
        if not isinstance(data, str):
            # For non-string data, convert to string and process
            text = str(data)
            original_data = data
        else:
            text = data
            original_data = data

        redacted_text = text
        detections: list[dict[str, Any]] = []

        # Check each PII type
        if "email" in self.targets:
            redacted_text, email_detections = self._process_emails(redacted_text)
            detections.extend(email_detections)

        if "phone" in self.targets:
            redacted_text, phone_detections = self._process_phones(redacted_text)
            detections.extend(phone_detections)

        if "credit_card" in self.targets:
            redacted_text, cc_detections = self._process_credit_cards(redacted_text)
            detections.extend(cc_detections)

        if "ssn" in self.targets:
            redacted_text, ssn_detections = self._process_ssns(redacted_text)
            detections.extend(ssn_detections)

        if "ip_address" in self.targets:
            redacted_text, ip_detections = self._process_ip_addresses(redacted_text)
            detections.extend(ip_detections)

        if "iban" in self.targets:
            redacted_text, iban_detections = self._process_ibans(redacted_text)
            detections.extend(iban_detections)

        if "address" in self.targets:
            redacted_text, addr_detections = self._process_addresses(redacted_text)
            detections.extend(addr_detections)

        # Process custom patterns
        for pattern in self.custom_patterns:
            redacted_text, custom_detections = self._process_pattern(
                redacted_text, pattern, "custom"
            )
            detections.extend(custom_detections)

        # Prepare result
        evidence = {
            "detections": detections,
            "detection_count": len(detections),
            "pii_types": list({d["type"] for d in detections}),
        }

        if detections:
            reasons = [f"Detected {len(detections)} PII instance(s)"]
            if self.mode == "remove":
                # Return the redacted text
                return Decision.transform(
                    original_data,
                    redacted_text,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            else:  # mask mode
                return Decision.transform(
                    original_data,
                    redacted_text,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )

        # No PII detected
        return Decision.allow(
            original_data,
            audit_id=ctx.audit_id,
            evidence=evidence,
        )

    def _process_emails(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process email addresses."""
        detections = []
        result = text

        for match in EMAIL_PATTERN.finditer(text):
            email = match.group()
            start, end = match.span()

            detections.append(
                {
                    "type": "email",
                    "original": email,
                    "start": start,
                    "end": end,
                }
            )

            if self.mode == "mask":
                replacement = mask_email(email)
            else:  # remove
                replacement = "[EMAIL_REMOVED]"

            result = result.replace(email, replacement, 1)

        return result, detections

    def _process_phones(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process phone numbers."""
        detections = []
        result = text

        for pattern in PHONE_PATTERNS:
            for match in pattern.finditer(text):
                phone = match.group()
                start, end = match.span()

                detections.append(
                    {
                        "type": "phone",
                        "original": phone,
                        "start": start,
                        "end": end,
                    }
                )

                if self.mode == "mask":
                    replacement = mask_phone(phone)
                else:  # remove
                    replacement = "[PHONE_REMOVED]"

                result = result.replace(phone, replacement, 1)

        return result, detections

    def _process_credit_cards(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process credit card numbers with Luhn validation."""
        detections = []
        result = text

        for pattern in CREDIT_CARD_PATTERNS:
            for match in pattern.finditer(text):
                card = match.group()
                start, end = match.span()

                # Validate with Luhn algorithm
                if luhn_check(card):
                    detections.append(
                        {
                            "type": "credit_card",
                            "original": card,
                            "start": start,
                            "end": end,
                        }
                    )

                    if self.mode == "mask":
                        replacement = mask_credit_card(card)
                    else:  # remove
                        replacement = "[CARD_REMOVED]"

                    result = result.replace(card, replacement, 1)

        return result, detections

    def _process_ssns(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process Social Security Numbers."""
        detections = []
        result = text

        for match in SSN_PATTERN.finditer(text):
            ssn = match.group()
            start, end = match.span()

            detections.append(
                {
                    "type": "ssn",
                    "original": ssn,
                    "start": start,
                    "end": end,
                }
            )

            if self.mode == "mask":
                replacement = mask_text(ssn, 3, 2)
            else:  # remove
                replacement = "[SSN_REMOVED]"

            result = result.replace(ssn, replacement, 1)

        return result, detections

    def _process_ip_addresses(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process IP addresses."""
        detections = []
        result = text

        for pattern in [IPV4_PATTERN, IPV6_PATTERN]:
            for match in pattern.finditer(text):
                ip = match.group()
                start, end = match.span()

                detections.append(
                    {
                        "type": "ip_address",
                        "original": ip,
                        "start": start,
                        "end": end,
                    }
                )

                if self.mode == "mask":
                    replacement = mask_text(ip, 2, 2)
                else:  # remove
                    replacement = "[IP_REMOVED]"

                result = result.replace(ip, replacement, 1)

        return result, detections

    def _process_ibans(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process IBAN numbers."""
        detections = []
        result = text

        for match in IBAN_PATTERN.finditer(text):
            iban = match.group()
            start, end = match.span()

            detections.append(
                {
                    "type": "iban",
                    "original": iban,
                    "start": start,
                    "end": end,
                }
            )

            if self.mode == "mask":
                replacement = mask_text(iban, 4, 4)
            else:  # remove
                replacement = "[IBAN_REMOVED]"

            result = result.replace(iban, replacement, 1)

        return result, detections

    def _process_addresses(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process addresses."""
        detections = []
        result = text

        for pattern in ADDRESS_PATTERNS:
            for match in pattern.finditer(text):
                address = match.group()
                start, end = match.span()

                detections.append(
                    {
                        "type": "address",
                        "original": address,
                        "start": start,
                        "end": end,
                    }
                )

                if self.mode == "mask":
                    replacement = mask_text(address, 2, 2)
                else:  # remove
                    replacement = "[ADDRESS_REMOVED]"

                result = result.replace(address, replacement, 1)

        return result, detections

    def _process_pattern(
        self, text: str, pattern: Pattern[str], pii_type: str
    ) -> tuple[str, list[dict[str, Any]]]:
        """Process a custom regex pattern."""
        detections = []
        result = text

        for match in pattern.finditer(text):
            matched_text = match.group()
            start, end = match.span()

            detections.append(
                {
                    "type": pii_type,
                    "original": matched_text,
                    "start": start,
                    "end": end,
                }
            )

            if self.mode == "mask":
                replacement = mask_text(matched_text)
            else:  # remove
                replacement = f"[{pii_type.upper()}_REMOVED]"

            result = result.replace(matched_text, replacement, 1)

        return result, detections

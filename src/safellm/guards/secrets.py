"""Secrets detection and masking guard."""

from __future__ import annotations

from typing import Any

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard
from ..utils.patterns import (
    API_KEY_PATTERNS,
    JWT_PATTERN,
    PASSWORD_INDICATORS,
    mask_api_key,
)


class SecretMaskGuard(BaseGuard):
    """Guard that detects and masks secrets like API keys, tokens, and passwords."""

    def __init__(
        self,
        vendors: list[str] | None = None,
        custom_patterns: list[tuple[str, str]] | None = None,  # (name, pattern)
    ) -> None:
        """Initialize the secrets masking guard.
        
        Args:
            vendors: List of vendor names to detect (None = all supported)
            custom_patterns: Additional patterns as (name, regex_pattern) tuples
        """
        self.vendors = vendors
        self.custom_patterns = custom_patterns or []

        # Map vendor names to their patterns
        self.vendor_patterns = {
            "stripe": [p for p in API_KEY_PATTERNS if "sk_" in p.pattern],
            "aws": [p for p in API_KEY_PATTERNS if "AKIA" in p.pattern],
            "google": [p for p in API_KEY_PATTERNS if "AIza" in p.pattern],
            "github": [p for p in API_KEY_PATTERNS if "gh" in p.pattern],
            "slack": [p for p in API_KEY_PATTERNS if "xox" in p.pattern],
        }

    @property
    def name(self) -> str:
        return "secret_mask"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Detect and mask secrets in the data."""
        if not isinstance(data, str):
            text = str(data)
            original_data = data
        else:
            text = data
            original_data = data

        masked_text = text
        detections: list[dict[str, Any]] = []

        # Detect API keys
        masked_text, api_detections = self._process_api_keys(masked_text)
        detections.extend(api_detections)

        # Detect JWT tokens
        masked_text, jwt_detections = self._process_jwt_tokens(masked_text)
        detections.extend(jwt_detections)

        # Detect password patterns
        masked_text, pwd_detections = self._process_passwords(masked_text)
        detections.extend(pwd_detections)

        # Process custom patterns
        for name, pattern_str in self.custom_patterns:
            import re
            pattern = re.compile(pattern_str)
            masked_text, custom_detections = self._process_pattern(
                masked_text, pattern, name
            )
            detections.extend(custom_detections)

        # Prepare result
        evidence = {
            "detections": detections,
            "detection_count": len(detections),
            "secret_types": list(set(d["type"] for d in detections)),
        }

        if detections:
            reasons = [f"Detected {len(detections)} secret(s)"]
            return Decision.transform(
                original_data,
                masked_text,
                reasons,
                audit_id=ctx.audit_id,
                evidence=evidence,
            )

        # No secrets detected
        return Decision.allow(
            original_data,
            audit_id=ctx.audit_id,
            evidence=evidence,
        )

    def _process_api_keys(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process API keys."""
        detections = []
        result = text

        patterns_to_check = []
        
        if self.vendors is None:
            # Check all patterns
            patterns_to_check = API_KEY_PATTERNS
        else:
            # Check only specified vendors
            for vendor in self.vendors:
                if vendor in self.vendor_patterns:
                    patterns_to_check.extend(self.vendor_patterns[vendor])

        for pattern in patterns_to_check:
            for match in pattern.finditer(text):
                key = match.group()
                start, end = match.span()
                
                # Determine the vendor type
                vendor_type = self._identify_vendor(key)
                
                detections.append({
                    "type": "api_key",
                    "vendor": vendor_type,
                    "original": key,
                    "start": start,
                    "end": end,
                })

                masked_key = mask_api_key(key)
                result = result.replace(key, masked_key, 1)

        return result, detections

    def _process_jwt_tokens(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process JWT tokens."""
        detections = []
        result = text

        for match in JWT_PATTERN.finditer(text):
            token = match.group()
            start, end = match.span()
            
            detections.append({
                "type": "jwt_token",
                "original": token,
                "start": start,
                "end": end,
            })

            # Mask the JWT (keep header visible, mask payload and signature)
            parts = token.split(".")
            if len(parts) == 3:
                masked_token = f"{parts[0]}.{'*' * 20}.{'*' * 20}"
            else:
                masked_token = mask_api_key(token)
            
            result = result.replace(token, masked_token, 1)

        return result, detections

    def _process_passwords(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Process password indicators."""
        detections = []
        result = text

        for match in PASSWORD_INDICATORS.finditer(text):
            full_match = match.group()
            password = match.group(1) if match.groups() else ""
            start, end = match.span()
            
            if password and len(password) > 2:  # Avoid false positives
                detections.append({
                    "type": "password",
                    "original": password,
                    "full_match": full_match,
                    "start": start,
                    "end": end,
                })

                # Replace the password part with asterisks
                masked_password = "*" * min(8, len(password))
                masked_full = full_match.replace(password, masked_password)
                result = result.replace(full_match, masked_full, 1)

        return result, detections

    def _process_pattern(
        self, text: str, pattern, secret_type: str
    ) -> tuple[str, list[dict[str, Any]]]:
        """Process a custom pattern."""
        detections = []
        result = text

        for match in pattern.finditer(text):
            secret = match.group()
            start, end = match.span()
            
            detections.append({
                "type": secret_type,
                "original": secret,
                "start": start,
                "end": end,
            })

            masked_secret = mask_api_key(secret)
            result = result.replace(secret, masked_secret, 1)

        return result, detections

    def _identify_vendor(self, key: str) -> str:
        """Identify the vendor type based on the key format."""
        if key.startswith("sk_live_") or key.startswith("sk_test_"):
            return "stripe"
        elif key.startswith("AKIA"):
            return "aws"
        elif key.startswith("AIza"):
            return "google"
        elif key.startswith("ghp_") or key.startswith("gho_"):
            return "github"
        elif key.startswith("xoxb-") or key.startswith("xoxp-"):
            return "slack"
        else:
            return "unknown"

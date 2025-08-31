"""Toxicity detection guard for harmful content."""

from __future__ import annotations

import re
from typing import Any, Literal

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard


class ToxicityGuard(BaseGuard):
    """Guard that detects toxic, harmful, or offensive content."""

    # Extended toxic patterns (in production, use ML-based toxicity detection)
    TOXIC_PATTERNS = {
        "threats": [
            r'\b(?:kill|murder|hurt|harm|attack|destroy|eliminate)\s+(?:you|him|her|them|myself)\b',
            r'\b(?:i|we|they)\s+(?:will|gonna|going to)\s+(?:kill|hurt|harm|attack)\b',
            r'\b(?:death|violence|harm)\s+(?:threat|warning)\b',
        ],
        "harassment": [
            r'\b(?:stupid|idiot|moron|retard|loser|pathetic|worthless|useless)\b',
            r'\b(?:shut up|go away|get lost|f\*ck off|piss off)\b',
            r'\b(?:hate|despise|can\'t stand)\s+(?:you|people like you)\b',
        ],
        "discrimination": [
            r'\b(?:all|those|these)\s+(?:people|guys|women|men)\s+(?:are|should be)\s+(?:banned|eliminated|removed)\b',
            r'\b(?:inferior|superior|better|worse)\s+(?:race|gender|religion|nationality)\b',
        ],
        "self_harm": [
            r'\b(?:kill|hurt|harm|cut|burn)\s+(?:myself|yourself)\b',
            r'\b(?:suicide|self-harm|self harm|end it all)\b',
            r'\b(?:want to die|wish i was dead|life is not worth)\b',
        ],
        "extremism": [
            r'\b(?:terrorist|terrorism|bomb|explosive|weapon)\b',
            r'\b(?:extremist|radical|jihad|crusade)\s+(?:attack|action|movement)\b',
        ],
        "adult_content": [
            r'\b(?:explicit|graphic|sexual|pornographic)\s+(?:content|material|image)\b',
            r'\b(?:sex|sexual|nude|naked|porn)\b.*\b(?:minor|child|kid|underage)\b',
        ],
    }

    # Severity levels
    SEVERITY_WEIGHTS = {
        "threats": 1.0,
        "self_harm": 1.0,
        "extremism": 0.9,
        "adult_content": 0.8,
        "harassment": 0.7,
        "discrimination": 0.6,
    }

    def __init__(
        self,
        action: Literal["block", "flag", "quarantine"] = "block",
        severity_threshold: float = 0.6,
        categories: list[str] | None = None,
        custom_patterns: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize the toxicity guard.

        Args:
            action: What to do when toxicity is detected
            severity_threshold: Minimum severity score to trigger action (0.0 to 1.0)
            categories: List of toxicity categories to check (if None, check all)
            custom_patterns: Additional custom toxic patterns by category
        """
        self.action = action
        self.severity_threshold = severity_threshold
        self.categories = set(categories) if categories else set(self.TOXIC_PATTERNS.keys())

        # Combine default and custom patterns
        self.patterns = {}
        for category in self.categories:
            patterns = self.TOXIC_PATTERNS.get(category, [])
            if custom_patterns and category in custom_patterns:
                patterns.extend(custom_patterns[category])

            # Compile regex patterns
            self.patterns[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    @property
    def name(self) -> str:
        return "toxicity"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Check for toxic content."""
        if not isinstance(data, str):
            text = str(data)
        else:
            text = data

        # Detect toxic content
        detections = self._detect_toxicity(text)
        severity_score = self._calculate_severity(detections)

        evidence = {
            "detections": detections,
            "severity_score": severity_score,
            "severity_threshold": self.severity_threshold,
            "categories_checked": list(self.categories),
        }

        if severity_score >= self.severity_threshold:
            categories_found = list({d["category"] for d in detections})
            reasons = [f"Toxic content detected (severity: {severity_score:.2f})"]
            reasons.append(f"Categories: {', '.join(categories_found)}")

            evidence["triggered_categories"] = categories_found

            if self.action == "block":
                return Decision.deny(
                    data,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            elif self.action == "quarantine":
                # Mark for human review
                return Decision.retry(
                    data,
                    reasons + ["Content flagged for human review"],
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

    def _detect_toxicity(self, text: str) -> list[dict[str, Any]]:
        """Detect toxic patterns in text."""
        detections = []

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = list(pattern.finditer(text))
                for match in matches:
                    detections.append({
                        "category": category,
                        "pattern": pattern.pattern,
                        "match": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "severity": self.SEVERITY_WEIGHTS.get(category, 0.5),
                    })

        return detections

    def _calculate_severity(self, detections: list[dict[str, Any]]) -> float:
        """Calculate overall severity score from detections."""
        if not detections:
            return 0.0

        # Calculate weighted average severity
        total_weight = 0.0
        weighted_severity = 0.0

        # Group by category to avoid over-weighting repeated patterns
        category_severities = {}
        for detection in detections:
            category = detection["category"]
            severity = detection["severity"]

            if category not in category_severities:
                category_severities[category] = []
            category_severities[category].append(severity)

        # Take maximum severity per category
        for _category, severities in category_severities.items():
            max_severity = max(severities)
            weight = len(severities)  # More matches = higher weight

            weighted_severity += max_severity * weight
            total_weight += weight

        # Normalize to 0-1 range
        if total_weight == 0:
            return 0.0

        base_score = weighted_severity / total_weight

        # Apply bonus for multiple categories
        category_bonus = min(0.3, (len(category_severities) - 1) * 0.1)

        return min(1.0, base_score + category_bonus)

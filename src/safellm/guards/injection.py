"""Prompt injection detection guard."""

from __future__ import annotations

import re
from typing import Any, Literal

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard


class PromptInjectionGuard(BaseGuard):
    """Guard that detects prompt injection and jailbreak attempts."""

    # Prompt injection patterns
    INJECTION_PATTERNS = {
        "role_manipulation": [
            r"(?i)(?:ignore|forget|disregard)\s+(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules|commands)",
            r"(?i)(?:you are now|from now on|starting now)\s+(?:a|an|acting as)\s+(?:different|new|another)",
            r"(?i)(?:pretend|act|behave|respond)\s+(?:as if|like|that)\s+(?:you are|you\'re)",
            r"(?i)(?:system|admin|developer|programmer|engineer)\s+(?:mode|access|override|bypass)",
        ],
        "instruction_override": [
            r"(?i)(?:new|updated|revised|different)\s+(?:instructions|prompt|system|rules)",
            r"(?i)(?:override|bypass|ignore|skip|disable)\s+(?:safety|security|restrictions|filters)",
            r"(?i)(?:end|stop|terminate|cancel)\s+(?:safety|security|protection|filtering)",
            r"(?i)(?:disable|turn off|remove|delete)\s+(?:guardrails|safety|security)",
            r"(?i)ignore\s+all\s+previous\s+instructions",
            r"(?i)(?:without|ignore)\s+(?:any\s+)?(?:limitations|restrictions|safety)",
        ],
        "jailbreak_attempts": [
            r"(?i)(?:DAN|do anything now|developer mode|god mode|admin mode)",
            r"(?i)(?:hypothetically|in theory|imagine if|what if|suppose)",
            r"(?i)(?:for educational|for research|for academic)\s+(?:purposes|reasons)",
            r"(?i)(?:just pretend|just imagine|just suppose|as an example)",
        ],
        "output_manipulation": [
            r"(?i)(?:output|respond|answer|reply)\s+(?:only|just|simply)\s+(?:yes|no|true|false)",
            r"(?i)(?:don\'t|do not|never)\s+(?:mention|say|include|add)\s+(?:warning|disclaimer|note)",
            r"(?i)(?:without|skip|omit)\s+(?:warnings|disclaimers|safety|notes)",
            r"(?i)(?:format|structure|present)\s+(?:as|like|in the form of)",
        ],
        "context_confusion": [
            r"(?i)(?:previous|earlier|above)\s+(?:conversation|chat|message|prompt)\s+(?:was|is)",
            r"(?i)(?:multiple|different|separate)\s+(?:conversations|chats|sessions)",
            r"(?i)(?:conversation|chat|session)\s+(?:history|context|background)",
            r"(?i)(?:remember|recall|think back)\s+(?:when|to when|about when)",
        ],
        "social_engineering": [
            r"(?i)(?:my|the)\s+(?:grandmother|mother|father|parent)\s+(?:used to|would)",
            r"(?i)(?:life|death|emergency|urgent|critical|important)\s+(?:situation|matter|case)",
            r"(?i)(?:please|help|assist|save)\s+(?:me|us|my|our)\s+(?:life|lives|situation)",
            r"(?i)(?:if you don\'t|unless you|you must|you have to|you need to)",
        ],
    }

    # Detection confidence weights
    PATTERN_WEIGHTS = {
        "role_manipulation": 0.9,
        "instruction_override": 1.0,
        "jailbreak_attempts": 0.8,
        "output_manipulation": 0.7,
        "context_confusion": 0.6,
        "social_engineering": 0.5,
    }

    def __init__(
        self,
        action: Literal["block", "flag", "sanitize"] = "block",
        confidence_threshold: float = 0.7,
        categories: list[str] | None = None,
        custom_patterns: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize the prompt injection guard.

        Args:
            action: What to do when injection is detected
            confidence_threshold: Minimum confidence to trigger action
            categories: List of injection categories to check
            custom_patterns: Additional custom injection patterns
        """
        self.action = action
        self.confidence_threshold = confidence_threshold
        self.categories = set(categories) if categories else set(self.INJECTION_PATTERNS.keys())

        # Combine default and custom patterns
        self.patterns = {}
        for category in self.categories:
            patterns = self.INJECTION_PATTERNS.get(category, [])
            if custom_patterns and category in custom_patterns:
                patterns.extend(custom_patterns[category])

            # Compile regex patterns
            self.patterns[category] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in patterns
            ]

    @property
    def name(self) -> str:
        return "prompt_injection"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Check for prompt injection attempts."""
        if not isinstance(data, str):
            text = str(data)
        else:
            text = data

        # Detect injection attempts
        detections = self._detect_injections(text)
        confidence_score = self._calculate_confidence(detections)

        evidence = {
            "detections": detections,
            "confidence_score": confidence_score,
            "confidence_threshold": self.confidence_threshold,
            "categories_checked": list(self.categories),
        }

        if confidence_score >= self.confidence_threshold:
            categories_found = list({d["category"] for d in detections})
            reasons = [f"Prompt injection detected (confidence: {confidence_score:.2f})"]
            reasons.append(f"Categories: {', '.join(categories_found)}")

            evidence["triggered_categories"] = categories_found

            if self.action == "block":
                return Decision.deny(
                    data,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            elif self.action == "sanitize":
                sanitized_text = self._sanitize_injections(text, detections)
                reasons.append("Injection attempts sanitized")
                return Decision.transform(
                    data,
                    sanitized_text,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            else:  # flag
                reasons.append("Content flagged but allowed")
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

    def _detect_injections(self, text: str) -> list[dict[str, Any]]:
        """Detect injection patterns in text."""
        detections = []

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = list(pattern.finditer(text))
                for match in matches:
                    detections.append(
                        {
                            "category": category,
                            "pattern": pattern.pattern,
                            "match": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                            "context": text[max(0, match.start() - 30) : match.end() + 30],
                            "weight": self.PATTERN_WEIGHTS.get(category, 0.5),
                        }
                    )

        return detections

    def _calculate_confidence(self, detections: list[dict[str, Any]]) -> float:
        """Calculate injection confidence score."""
        if not detections:
            return 0.0

        # Group by category to avoid over-weighting
        category_confidences: dict[str, list[float]] = {}
        for detection in detections:
            category = detection["category"]
            weight = detection["weight"]

            if category not in category_confidences:
                category_confidences[category] = []
            category_confidences[category].append(weight)

        # Calculate weighted confidence
        total_confidence = 0.0
        for _category, weights in category_confidences.items():
            # Take max weight per category, add bonus for multiple matches
            max_weight = max(weights)
            match_bonus = min(0.2, (len(weights) - 1) * 0.05)
            category_confidence = min(1.0, max_weight + match_bonus)
            total_confidence += category_confidence

        # Normalize and add multi-category bonus
        base_confidence = total_confidence / float(len(category_confidences))
        multi_category_bonus = min(0.3, (len(category_confidences) - 1) * 0.1)

        return float(min(1.0, base_confidence + multi_category_bonus))

    def _sanitize_injections(self, text: str, detections: list[dict[str, Any]]) -> str:
        """Sanitize injection attempts from text."""
        # Sort detections by start position in reverse order
        sorted_detections = sorted(detections, key=lambda x: x["start"], reverse=True)

        result = text
        for detection in sorted_detections:
            start = detection["start"]
            end = detection["end"]
            category = detection["category"]

            # Create appropriate sanitization
            if category in ["role_manipulation", "instruction_override"]:
                replacement = "[INSTRUCTION_OVERRIDE_REMOVED]"
            elif category == "jailbreak_attempts":
                replacement = "[JAILBREAK_ATTEMPT_REMOVED]"
            elif category == "output_manipulation":
                replacement = "[OUTPUT_MANIPULATION_REMOVED]"
            elif category == "context_confusion":
                replacement = "[CONTEXT_CONFUSION_REMOVED]"
            elif category == "social_engineering":
                replacement = "[SOCIAL_ENGINEERING_REMOVED]"
            else:
                replacement = "[INJECTION_ATTEMPT_REMOVED]"

            result = result[:start] + replacement + result[end:]

        return result

    def _is_potential_instruction(self, text: str) -> bool:
        """Check if text looks like an instruction or command."""
        instruction_indicators = [
            r"(?:^|\n)\s*(?:please|kindly|can you|could you|would you)",
            r"(?:^|\n)\s*(?:tell me|show me|explain|describe|list|generate)",
            r"(?:^|\n)\s*(?:write|create|make|build|design|develop)",
            r"(?:^|\n)\s*(?:ignore|forget|disregard|override|bypass)",
        ]

        for pattern in instruction_indicators:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                return True

        return False

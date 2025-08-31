"""Language detection and filtering guard."""

from __future__ import annotations

import re
from typing import Any, Literal

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard


class LanguageGuard(BaseGuard):
    """Guard that detects and filters content based on language."""

    # Basic language detection patterns (in production, use proper language detection library)
    LANGUAGE_PATTERNS = {
        "english": re.compile(r"\b(?:the|and|or|but|in|on|at|to|for|of|with|by)\b", re.IGNORECASE),
        "spanish": re.compile(r"\b(?:el|la|los|las|y|o|pero|en|de|con|por|para)\b", re.IGNORECASE),
        "french": re.compile(r"\b(?:le|la|les|et|ou|mais|dans|de|avec|par|pour)\b", re.IGNORECASE),
        "german": re.compile(r"\b(?:der|die|das|und|oder|aber|in|von|mit|zu|für)\b", re.IGNORECASE),
        "italian": re.compile(r"\b(?:il|la|gli|le|e|o|ma|in|di|con|per|da)\b", re.IGNORECASE),
        "portuguese": re.compile(r"\b(?:o|a|os|as|e|ou|mas|em|de|com|por|para)\b", re.IGNORECASE),
        "russian": re.compile(r"[а-яё]+", re.IGNORECASE),
        "chinese": re.compile(r"[\u4e00-\u9fff]+"),
        "japanese": re.compile(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+"),
        "korean": re.compile(r"[\uac00-\ud7af]+"),
        "arabic": re.compile(r"[\u0600-\u06ff]+"),
        "hindi": re.compile(r"[\u0900-\u097f]+"),
    }

    def __init__(
        self,
        allowed_languages: list[str] | None = None,
        blocked_languages: list[str] | None = None,
        action: Literal["block", "flag"] = "flag",
        min_confidence: float = 0.3,
    ) -> None:
        """Initialize the language guard.

        Args:
            allowed_languages: List of allowed language codes (if None, all are allowed)
            blocked_languages: List of blocked language codes
            action: What to do when non-allowed language is detected
            min_confidence: Minimum confidence threshold for detection
        """
        self.allowed_languages = set(allowed_languages) if allowed_languages else None
        self.blocked_languages = set(blocked_languages) if blocked_languages else set()
        self.action = action
        self.min_confidence = min_confidence

    @property
    def name(self) -> str:
        return "language"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Check the language of the content."""
        if not isinstance(data, str):
            text = str(data)
        else:
            text = data

        # Detect languages
        detected_languages = self._detect_languages(text)

        evidence = {
            "detected_languages": detected_languages,
            "text_length": len(text),
        }

        # Check if any detected language is blocked
        blocked_detected = []
        for lang_info in detected_languages:
            lang = lang_info["language"]
            confidence = lang_info["confidence"]

            if confidence >= self.min_confidence:
                if lang in self.blocked_languages:
                    blocked_detected.append(lang)
                elif self.allowed_languages and lang not in self.allowed_languages:
                    blocked_detected.append(lang)

        if blocked_detected:
            reasons = [f"Detected blocked/disallowed language(s): {', '.join(blocked_detected)}"]
            evidence["blocked_languages"] = blocked_detected

            if self.action == "block":
                return Decision.deny(
                    data,
                    reasons,
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

    def _detect_languages(self, text: str) -> list[dict[str, Any]]:
        """Detect languages in the text with basic pattern matching."""
        if not text.strip():
            return []

        results = []
        text_length = len(text)

        for language, pattern in self.LANGUAGE_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                # Calculate a simple confidence score
                match_chars = sum(len(match) for match in matches)
                confidence = min(1.0, match_chars / max(1, text_length * 0.1))

                if confidence > 0.1:  # Only include if there's some evidence
                    results.append(
                        {
                            "language": language,
                            "confidence": confidence,
                            "matches": len(matches),
                            "match_examples": matches[:3],  # First 3 matches as examples
                        }
                    )

        # Sort by confidence descending
        from typing import cast
        results.sort(key=lambda x: cast(float, x.get("confidence", 0.0)), reverse=True)
        return results

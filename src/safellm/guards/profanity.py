"""Profanity detection and filtering guard."""

from __future__ import annotations

from typing import Any, Literal

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard
from ..utils.patterns import contains_profanity, normalize_leet_speak


class ProfanityGuard(BaseGuard):
    """Guard that detects and handles profanity in text content."""

    def __init__(
        self,
        action: Literal["block", "mask", "flag"] = "mask",
        custom_words: set[str] | None = None,
        allowlist: set[str] | None = None,
    ) -> None:
        """Initialize the profanity guard.

        Args:
            action: How to handle profanity - 'block', 'mask', or 'flag'
            custom_words: Additional words to consider profanity
            allowlist: Words to exclude from profanity detection
        """
        self.action = action
        self.custom_words = custom_words or set()
        self.allowlist = allowlist or set()

    @property
    def name(self) -> str:
        return "profanity"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Check for profanity in the data."""
        if not isinstance(data, str):
            text = str(data)
            original_data = data
        else:
            text = data
            original_data = data

        # Check for profanity
        detections = self._detect_profanity(text)

        evidence = {
            "detections": detections,
            "detection_count": len(detections),
        }

        if detections:
            reasons = [f"Detected {len(detections)} profanity instance(s)"]

            if self.action == "block":
                return Decision.deny(
                    original_data,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            elif self.action == "mask":
                cleaned_text = self._mask_profanity(text, detections)
                return Decision.transform(
                    original_data,
                    cleaned_text,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            else:  # flag
                return Decision.allow(
                    original_data,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )

        # No profanity detected
        return Decision.allow(
            original_data,
            audit_id=ctx.audit_id,
            evidence=evidence,
        )

    def _detect_profanity(self, text: str) -> list[dict[str, Any]]:
        """Detect profanity in text and return detection details."""
        detections = []

        # Normalize text for detection
        normalized = normalize_leet_speak(text.lower())
        words = normalized.split()

        # Check each word
        for i, word in enumerate(words):
            # Remove punctuation for checking
            clean_word = ''.join(c for c in word if c.isalnum())

            if self._is_profanity(clean_word):
                # Find the original word position in the text
                original_words = text.split()
                if i < len(original_words):
                    original_word = original_words[i]
                    start_pos = text.find(original_word)

                    detections.append({
                        "word": original_word,
                        "normalized": clean_word,
                        "position": i,
                        "start": start_pos,
                        "end": start_pos + len(original_word),
                    })

        return detections

    def _is_profanity(self, word: str) -> bool:
        """Check if a word is considered profanity."""
        # Check allowlist first
        if word in self.allowlist:
            return False

        # Check custom words
        if word in self.custom_words:
            return True

        # Use the basic profanity detection from patterns
        return contains_profanity(word)

    def _mask_profanity(self, text: str, detections: list[dict[str, Any]]) -> str:
        """Mask profanity in text based on detections."""
        result = text

        # Sort detections by start position in reverse order
        # so we can replace from end to beginning without affecting positions
        sorted_detections = sorted(detections, key=lambda x: x["start"], reverse=True)

        for detection in sorted_detections:
            word = detection["word"]
            start = detection["start"]
            end = detection["end"]

            # Create mask (keep first letter, mask the rest)
            if len(word) > 1:
                masked = word[0] + "*" * (len(word) - 1)
            else:
                masked = "*"

            # Replace in the result
            result = result[:start] + masked + result[end:]

        return result

"""Content similarity and duplicate detection guard."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Literal

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard


class SimilarityGuard(BaseGuard):
    """Guard that detects duplicate or highly similar content."""

    def __init__(
        self,
        similarity_threshold: float = 0.8,
        action: Literal["block", "flag"] = "flag",
        max_history_size: int = 1000,
        use_fuzzy_matching: bool = True,
    ) -> None:
        """Initialize the similarity guard.

        Args:
            similarity_threshold: Similarity threshold (0.0 to 1.0)
            action: What to do when similarity is detected
            max_history_size: Maximum number of content hashes to store
            use_fuzzy_matching: Whether to use fuzzy text matching
        """
        self.similarity_threshold = similarity_threshold
        self.action = action
        self.max_history_size = max_history_size
        self.use_fuzzy_matching = use_fuzzy_matching

        # In-memory storage (in production, use Redis or database)
        self.content_hashes: dict[str, dict[str, Any]] = {}
        self.normalized_content: dict[str, str] = {}

    @property
    def name(self) -> str:
        return "similarity"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Check for content similarity."""
        if not isinstance(data, str):
            text = str(data)
        else:
            text = data

        # Generate hash for exact duplicate detection
        content_hash = hashlib.md5(text.encode()).hexdigest()

        # Normalize text for fuzzy matching
        normalized = self._normalize_text(text)
        normalized_hash = hashlib.md5(normalized.encode()).hexdigest()

        evidence = {
            "content_hash": content_hash,
            "normalized_hash": normalized_hash,
            "text_length": len(text),
            "normalized_length": len(normalized),
        }

        # Check for exact duplicates
        if content_hash in self.content_hashes:
            previous_info = self.content_hashes[content_hash]
            reasons = ["Exact duplicate content detected"]
            evidence.update({
                "duplicate_type": "exact",
                "previous_audit_id": previous_info.get("audit_id"),
                "previous_timestamp": previous_info.get("timestamp"),
            })

            return self._handle_similarity_detection(data, reasons, evidence, ctx)

        # Check for fuzzy duplicates if enabled
        if self.use_fuzzy_matching:
            similar_content = self._find_similar_content(normalized)
            if similar_content:
                similarity_score = similar_content["similarity"]
                if similarity_score >= self.similarity_threshold:
                    reasons = [f"Similar content detected (similarity: {similarity_score:.2f})"]
                    evidence.update({
                        "duplicate_type": "fuzzy",
                        "similarity_score": similarity_score,
                        "similar_hash": similar_content["hash"],
                        "similar_audit_id": similar_content.get("audit_id"),
                    })

                    result = self._handle_similarity_detection(data, reasons, evidence, ctx)
                    # Still store this content even if similar
                    self._store_content(content_hash, normalized_hash, normalized, ctx)
                    return result

        # Store content for future comparisons
        self._store_content(content_hash, normalized_hash, normalized, ctx)

        return Decision.allow(
            data,
            audit_id=ctx.audit_id,
            evidence=evidence,
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for fuzzy comparison."""
        # Convert to lowercase
        normalized = text.lower()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        # Remove punctuation (keep alphanumeric and spaces)
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

        # Remove common stop words for better similarity detection
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
        }
        words = normalized.split()
        filtered_words = [word for word in words if word not in stop_words]

        return ' '.join(filtered_words).strip()

    def _find_similar_content(self, normalized_text: str) -> dict[str, Any] | None:
        """Find similar content using simple text similarity."""
        if not normalized_text:
            return None

        best_similarity = 0.0
        best_match = None

        for stored_hash, stored_text in self.normalized_content.items():
            similarity = self._calculate_similarity(normalized_text, stored_text)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    "hash": stored_hash,
                    "similarity": similarity,
                    "text": stored_text,
                }

                # Also get metadata if available
                for _content_hash, info in self.content_hashes.items():
                    if info.get("normalized_hash") == stored_hash:
                        best_match.update(info)
                        break

        return best_match if best_similarity > 0 else None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using simple metrics."""
        if not text1 or not text2:
            return 0.0

        # Simple character-based similarity (Jaccard-like)
        set1 = set(text1.split())
        set2 = set(text2.split())

        if not set1 and not set2:
            return 1.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _store_content(self, content_hash: str, normalized_hash: str, normalized_text: str, ctx: Context) -> None:
        """Store content for future comparison."""
        import time

        # Limit storage size
        if len(self.content_hashes) >= self.max_history_size:
            # Remove oldest entries (simple FIFO)
            oldest_hash = next(iter(self.content_hashes))
            del self.content_hashes[oldest_hash]

            # Also clean up normalized content
            if oldest_hash in self.normalized_content:
                del self.normalized_content[oldest_hash]

        self.content_hashes[content_hash] = {
            "audit_id": ctx.audit_id,
            "timestamp": time.time(),
            "normalized_hash": normalized_hash,
            "user_role": ctx.user_role,
            "model": ctx.model,
        }

        self.normalized_content[normalized_hash] = normalized_text

    def _handle_similarity_detection(
        self, data: Any, reasons: list[str], evidence: dict[str, Any], ctx: Context
    ) -> Decision:
        """Handle similarity detection based on action setting."""
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

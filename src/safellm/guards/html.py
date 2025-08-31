"""HTML and Markdown sanitization guards."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard

if TYPE_CHECKING:
    pass


class HtmlSanitizerGuard(BaseGuard):
    """Guard that sanitizes HTML content to prevent XSS and other attacks."""

    # Default safe tags and attributes
    DEFAULT_TAGS = [
        "p",
        "br",
        "strong",
        "em",
        "u",
        "b",
        "i",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "blockquote",
        "code",
        "pre",
    ]

    DEFAULT_ATTRIBUTES = {
        "*": ["class", "id"],
        "a": ["href", "title"],
        "img": ["src", "alt", "title", "width", "height"],
    }

    def __init__(
        self,
        policy: str = "strict",
        allowed_tags: list[str] | None = None,
        allowed_attributes: dict[str, list[str]] | None = None,
        strip_comments: bool = True,
    ) -> None:
        """Initialize the HTML sanitizer guard.

        Args:
            policy: Sanitization policy - 'strict', 'moderate', or 'custom'
            allowed_tags: List of allowed HTML tags (for custom policy)
            allowed_attributes: Dict of tag -> allowed attributes (for custom policy)
            strip_comments: Whether to remove HTML comments
        """
        self.policy = policy
        self.strip_comments = strip_comments

        if policy == "strict":
            self.allowed_tags = ["p", "br", "strong", "em"]
            self.allowed_attributes = {}
        elif policy == "moderate":
            self.allowed_tags = self.DEFAULT_TAGS
            self.allowed_attributes = self.DEFAULT_ATTRIBUTES
        elif policy == "custom":
            self.allowed_tags = allowed_tags or []
            self.allowed_attributes = allowed_attributes or {}
        else:
            raise ValueError(f"Unknown policy: {policy}")

        # Try to import bleach for advanced sanitization
        self._has_bleach = False
        try:
            import bleach  # noqa: F401

            self._has_bleach = True
        except ImportError:
            pass

    @property
    def name(self) -> str:
        return "html_sanitizer"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Sanitize HTML content in the data."""
        if not isinstance(data, str):
            text = str(data)
            original_data = data
        else:
            text = data
            original_data = data

        # Check if the text contains HTML
        if not self._contains_html(text):
            return Decision.allow(
                original_data,
                audit_id=ctx.audit_id,
                evidence={"contains_html": False},
            )

        # Sanitize the HTML
        sanitized_text, issues = self._sanitize_html(text)

        evidence = {
            "contains_html": True,
            "sanitization_issues": issues,
            "issue_count": len(issues),
            "has_bleach": self._has_bleach,
        }

        if issues:
            reasons = [f"Sanitized HTML content: {len(issues)} issue(s) found"]
            return Decision.transform(
                original_data,
                sanitized_text,
                reasons,
                audit_id=ctx.audit_id,
                evidence=evidence,
            )

        # No issues found, but we processed HTML
        return Decision.allow(
            sanitized_text,
            audit_id=ctx.audit_id,
            evidence=evidence,
        )

    def _contains_html(self, text: str) -> bool:
        """Check if text contains HTML tags."""
        html_pattern = re.compile(r"<[^>]+>")
        return bool(html_pattern.search(text))

    def _sanitize_html(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Sanitize HTML content and return issues found."""

        if self._has_bleach:
            return self._sanitize_with_bleach(text)
        else:
            return self._sanitize_basic(text)

    def _sanitize_with_bleach(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Sanitize using bleach library."""
        import bleach

        issues = []

        # Track what was removed
        original_tags = self._extract_tags(text)

        # Sanitize
        sanitized = bleach.clean(
            text,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            strip=True,
            strip_comments=self.strip_comments,
        )

        # Check what was changed
        sanitized_tags = self._extract_tags(sanitized)
        removed_tags = original_tags - sanitized_tags

        if removed_tags:
            issues.append(
                {
                    "type": "removed_tags",
                    "tags": list(removed_tags),
                    "count": len(removed_tags),
                }
            )

        if len(sanitized) != len(text):
            issues.append(
                {
                    "type": "content_modified",
                    "original_length": len(text),
                    "sanitized_length": len(sanitized),
                }
            )

        return sanitized, issues

    def _sanitize_basic(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Basic HTML sanitization without bleach."""
        issues = []
        result = text

        # Remove all script and style tags
        script_pattern = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
        style_pattern = re.compile(r"<style[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)

        scripts_found = script_pattern.findall(result)
        styles_found = style_pattern.findall(result)

        if scripts_found:
            issues.append(
                {
                    "type": "removed_scripts",
                    "count": len(scripts_found),
                }
            )
            result = script_pattern.sub("", result)

        if styles_found:
            issues.append(
                {
                    "type": "removed_styles",
                    "count": len(styles_found),
                }
            )
            result = style_pattern.sub("", result)

        # Remove dangerous attributes
        dangerous_attrs = ["onclick", "onload", "onmouseover", "onerror", "javascript:"]
        for attr in dangerous_attrs:
            pattern = re.compile(f"{attr}[^>]*", re.IGNORECASE)
            if pattern.search(result):
                issues.append(
                    {
                        "type": "removed_dangerous_attribute",
                        "attribute": attr,
                    }
                )
                result = pattern.sub("", result)

        # Remove comments if requested
        if self.strip_comments:
            comment_pattern = re.compile(r"<!--.*?-->", re.DOTALL)
            comments_found = comment_pattern.findall(result)
            if comments_found:
                issues.append(
                    {
                        "type": "removed_comments",
                        "count": len(comments_found),
                    }
                )
                result = comment_pattern.sub("", result)

        # If strict policy, remove all tags except allowed ones
        if self.policy == "strict":
            all_tags = self._extract_tags(result)
            disallowed_tags = all_tags - set(self.allowed_tags)

            for tag in disallowed_tags:
                # Remove opening and closing tags
                tag_pattern = re.compile(f"</?{re.escape(tag)}[^>]*>", re.IGNORECASE)
                if tag_pattern.search(result):
                    issues.append(
                        {
                            "type": "removed_disallowed_tag",
                            "tag": tag,
                        }
                    )
                    result = tag_pattern.sub("", result)

        return result, issues

    def _extract_tags(self, text: str) -> set[str]:
        """Extract all HTML tag names from text."""
        tag_pattern = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)[^>]*>")
        return {match.group(1).lower() for match in tag_pattern.finditer(text)}


class MarkdownSanitizerGuard(BaseGuard):
    """Guard that sanitizes Markdown content."""

    def __init__(
        self,
        allow_html: bool = False,
        allowed_tags: list[str] | None = None,
    ) -> None:
        """Initialize the Markdown sanitizer guard.

        Args:
            allow_html: Whether to allow HTML tags in Markdown
            allowed_tags: List of allowed HTML tags (if allow_html is True)
        """
        self.allow_html = allow_html
        self.allowed_tags = allowed_tags or []

    @property
    def name(self) -> str:
        return "markdown_sanitizer"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Sanitize Markdown content in the data."""
        if not isinstance(data, str):
            text = str(data)
            original_data = data
        else:
            text = data
            original_data = data

        sanitized_text, issues = self._sanitize_markdown(text)

        evidence = {
            "sanitization_issues": issues,
            "issue_count": len(issues),
            "allow_html": self.allow_html,
        }

        if issues:
            reasons = [f"Sanitized Markdown content: {len(issues)} issue(s) found"]
            return Decision.transform(
                original_data,
                sanitized_text,
                reasons,
                audit_id=ctx.audit_id,
                evidence=evidence,
            )

        return Decision.allow(
            original_data,
            audit_id=ctx.audit_id,
            evidence=evidence,
        )

    def _sanitize_markdown(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """Sanitize Markdown content."""
        issues = []
        result = text

        # Remove potentially dangerous Markdown patterns
        # 1. Javascript links
        js_link_pattern = re.compile(r"\[([^\]]+)\]\s*\(\s*javascript:[^)]+\)", re.IGNORECASE)
        js_links = js_link_pattern.findall(result)
        if js_links:
            issues.append(
                {
                    "type": "removed_javascript_links",
                    "count": len(js_links),
                }
            )
            result = js_link_pattern.sub(r"[\1](javascript-removed)", result)

        # 2. Data URLs that might contain scripts
        data_url_pattern = re.compile(r"\[([^\]]+)\]\s*\(\s*data:[^)]+\)", re.IGNORECASE)
        data_urls = data_url_pattern.findall(result)
        if data_urls:
            issues.append(
                {
                    "type": "removed_data_urls",
                    "count": len(data_urls),
                }
            )
            result = data_url_pattern.sub(r"[\1](data-url-removed)", result)

        # 3. If HTML is not allowed, remove HTML tags
        if not self.allow_html:
            html_pattern = re.compile(r"<[^>]+>")
            html_tags = html_pattern.findall(result)
            if html_tags:
                issues.append(
                    {
                        "type": "removed_html_tags",
                        "count": len(html_tags),
                    }
                )
                result = html_pattern.sub("", result)

        return result, issues

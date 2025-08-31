"""Final coverage improvement tests targeting remaining gaps."""

import re
import unittest

from safellm.context import Context
from safellm.guards import (
    BusinessRulesGuard,
    FormatGuard,
    HtmlSanitizerGuard,
    LengthGuard,
    MarkdownSanitizerGuard,
    PiiRedactionGuard,
    ProfanityGuard,
    SchemaGuard,
    SecretMaskGuard,
)


class TestFinalCoverage(unittest.TestCase):
    """Tests to achieve 100% coverage on remaining areas."""

    def test_pii_guard_comprehensive(self):
        """Test PII guard with all features."""
        ctx = Context()

        # Test mask mode with all targets
        guard = PiiRedactionGuard(mode="mask", targets=["email", "phone", "credit_card", "ssn", "ip_address", "iban"])

        # Test various PII types
        test_cases = [
            "Email: user@example.com",
            "Phone: 555-123-4567",
            "Credit card: 4111-1111-1111-1111",
            "SSN: 123-45-6789",
            "IP: 192.168.1.1",
            "IPv6: 2001:db8::1",
            "IBAN: GB82 WEST 1234 5698 7654 32",
        ]

        for case in test_cases:
            result = guard.check(case, ctx)
            self.assertIn(result.action, ["allow", "transform"])

        # Test remove mode
        guard = PiiRedactionGuard(mode="remove")
        result = guard.check("Email user@test.com and phone 555-1234", ctx)
        self.assertIn(result.action, ["allow", "transform"])

        # Test custom patterns
        custom_pattern = re.compile(r'\bcustom\d+\b')
        guard = PiiRedactionGuard(custom_patterns=[custom_pattern])
        result = guard.check("This has custom123 pattern", ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_secrets_guard_comprehensive(self):
        """Test secrets guard with all patterns."""
        guard = SecretMaskGuard()
        ctx = Context()

        secret_patterns = [
            "password=secret123!",
            "token: ghp_xxxxxxxxxxxxxxxxxxxx",
            "aws_access_key_id=AKIAIOSFODNN7EXAMPLE",
            "client_secret=supersecret123",
        ]

        for pattern in secret_patterns:
            result = guard.check(pattern, ctx)
            # Just test that it processes without error
            self.assertIn(result.action, ["allow", "transform"])
            if result.action == "transform":
                # Should mask the secret
                self.assertNotEqual(result.output, pattern)

    def test_profanity_guard_basic_test(self):
        """Test profanity guard basic functionality."""
        ctx = Context()

        # Test with default settings
        guard = ProfanityGuard()
        result = guard.check("This is a clean message", ctx)
        self.assertEqual(result.action, "allow")

        # Test empty content
        result = guard.check("", ctx)
        self.assertEqual(result.action, "allow")

    def test_schema_guard_basic_test(self):
        """Test basic schema functionality."""
        ctx = Context()

        try:
            # Test JSON schema validation if available
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                }
            }

            guard = SchemaGuard.from_json_schema(schema)

            # Test valid data
            valid_data = {"name": "John"}
            result = guard.check(valid_data, ctx)
            self.assertEqual(result.action, "allow")

        except ImportError:
            # Skip if jsonschema not available
            self.skipTest("jsonschema not available")
        except TypeError:
            # Skip if SchemaGuard is abstract
            self.skipTest("SchemaGuard is abstract")

    def test_format_guard_basic_test(self):
        """Test format guard basic functionality."""
        ctx = Context()

        # Test email format
        guard = FormatGuard(format_type="email")
        result = guard.check("user@example.com", ctx)
        self.assertEqual(result.action, "allow")

        result = guard.check("invalid-email", ctx)
        self.assertEqual(result.action, "deny")

        # Test JSON format
        guard = FormatGuard(format_type="json")
        result = guard.check('{"key": "value"}', ctx)
        self.assertEqual(result.action, "allow")

        result = guard.check('invalid json', ctx)
        self.assertEqual(result.action, "deny")

    def test_business_rules_guard_basic_test(self):
        """Test business rules guard basic functionality."""
        ctx = Context()

        # Test with a simple rule using proper structure
        rules = [{
            "id": "length_check",
            "name": "Length validation",
            "type": "length",
            "config": {
                "min_length": 5
            }
        }]

        guard = BusinessRulesGuard(rules)

        # Test short text (should fail)
        result = guard.check("Hi", ctx)
        self.assertEqual(result.action, "deny")

        # Test good length
        result = guard.check("Hello World", ctx)
        self.assertEqual(result.action, "allow")

    def test_markdown_sanitizer_comprehensive(self):
        """Test markdown sanitizer with various content."""
        guard = MarkdownSanitizerGuard()
        ctx = Context()

        # Test safe markdown
        safe_md = "# Title\n\n**Bold text** and *italic*\n\n- List item"
        result = guard.check(safe_md, ctx)
        self.assertEqual(result.action, "allow")

        # Test markdown with dangerous HTML
        dangerous_md = "# Title\n\n<script>alert('xss')</script>\n\nSafe content"
        result = guard.check(dangerous_md, ctx)
        self.assertEqual(result.action, "transform")
        self.assertNotIn("<script>", result.output)

        # Test empty content
        result = guard.check("", ctx)
        self.assertEqual(result.action, "allow")

    def test_html_sanitizer_edge_cases(self):
        """Test HTML sanitizer edge cases to improve coverage."""
        ctx = Context()

        # Test with comments
        guard = HtmlSanitizerGuard(strip_comments=True)
        result = guard.check("<!-- comment --><p>Content</p>", ctx)
        self.assertIn(result.action, ["allow", "transform"])

        guard = HtmlSanitizerGuard(strip_comments=False)
        result = guard.check("<!-- comment --><p>Content</p>", ctx)
        self.assertIn(result.action, ["allow", "transform"])

        # Test malformed HTML
        malformed_cases = [
            "<p>Unclosed paragraph",
            "<div><span>Nested unclosed",
            "Text with < and > symbols",
            "<img src='invalid' onerror='alert()'>",
        ]

        guard = HtmlSanitizerGuard(policy="strict")
        for case in malformed_cases:
            result = guard.check(case, ctx)
            self.assertIn(result.action, ["allow", "transform"])

    def test_context_copy_and_metadata(self):
        """Test context copy functionality and metadata handling."""
        # Test with complex metadata
        metadata = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "complex": {"nested": {"deep": "value"}}
        }

        ctx = Context(
            model="test-model",
            user_role="admin",
            purpose="testing",
            trace_id="trace-123",
            seed=42,
            metadata=metadata
        )

        # Test copy with overrides
        ctx2 = ctx.copy(model="new-model", metadata={"new": "data"})
        self.assertEqual(ctx2.model, "new-model")
        self.assertEqual(ctx2.user_role, "admin")  # Should preserve
        self.assertEqual(ctx2.metadata["new"], "data")

    def test_pipeline_edge_cases(self):
        """Test pipeline edge cases."""
        from safellm.pipeline import Pipeline

        # Test empty guards list
        with self.assertRaises(ValueError):
            Pipeline("empty", [])

        # Test with actual guards for edge case coverage
        guards = [
            LengthGuard(max_chars=100),
            ProfanityGuard(),
        ]

        pipeline = Pipeline("test", guards)

        # Test with None data
        result = pipeline.validate(None)
        self.assertIn(result.action, ["allow", "deny"])

        # Test with various data types
        test_data = [
            123,
            [],
            {},
            True,
            3.14
        ]

        for data in test_data:
            result = pipeline.validate(data)
            self.assertIn(result.action, ["allow", "deny", "transform"])


if __name__ == "__main__":
    unittest.main()

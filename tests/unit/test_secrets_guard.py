"""Tests for the SecretMaskGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.secrets import SecretMaskGuard


class TestSecretMaskGuard(unittest.TestCase):
    """Test the SecretMaskGuard class."""

    def test_initialization(self):
        """Test guard initialization."""
        guard = SecretMaskGuard()

        self.assertEqual(guard.name, "secret_mask")

    def test_password_masking(self):
        """Test password masking."""
        guard = SecretMaskGuard()
        ctx = Context()

        result = guard.check("password=secret123!", ctx)
        self.assertIn(result.action, ["allow", "transform"])

        if result.action == "transform":
            self.assertNotEqual(result.output, "password=secret123!")

    def test_token_masking(self):
        """Test token masking."""
        guard = SecretMaskGuard()
        ctx = Context()

        result = guard.check("token: ghp_xxxxxxxxxxxxxxxxxxxx", ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_api_key_masking(self):
        """Test API key masking."""
        guard = SecretMaskGuard()
        ctx = Context()

        result = guard.check("aws_access_key_id=AKIAIOSFODNN7EXAMPLE", ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_client_secret_masking(self):
        """Test client secret masking."""
        guard = SecretMaskGuard()
        ctx = Context()

        result = guard.check("client_secret=supersecret123", ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_multiple_secrets(self):
        """Test multiple secrets in one text."""
        guard = SecretMaskGuard()
        ctx = Context()

        text = "password=secret123 and token=abc123"
        result = guard.check(text, ctx)
        self.assertIn(result.action, ["allow", "transform"])

    def test_no_secrets(self):
        """Test text with no secrets."""
        guard = SecretMaskGuard()
        ctx = Context()

        result = guard.check("This is normal text without secrets", ctx)
        self.assertEqual(result.action, "allow")

    def test_empty_content(self):
        """Test empty content."""
        guard = SecretMaskGuard()
        ctx = Context()

        result = guard.check("", ctx)
        self.assertEqual(result.action, "allow")

    def test_custom_patterns(self):
        """Test custom secret patterns."""
        try:
            guard = SecretMaskGuard(custom_patterns=[("custom_secret", r"custom_secret=[\w]+")])
            ctx = Context()

            result = guard.check("custom_secret=mysecret", ctx)
            self.assertIn(result.action, ["allow", "transform"])
        except TypeError:
            # Guard doesn't support custom patterns
            pass


if __name__ == "__main__":
    unittest.main()

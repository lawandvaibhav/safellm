"""Tests for the SchemaGuard class."""

import unittest

from safellm.context import Context
from safellm.guards.schema import SchemaGuard


class TestSchemaGuard(unittest.TestCase):
    """Test the SchemaGuard class."""

    def test_json_schema_initialization(self):
        """Test JSON schema guard initialization."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        guard = SchemaGuard.from_json_schema(schema)

        self.assertEqual(guard.name, "json_schema")
        self.assertEqual(guard.schema, schema)

    def test_valid_json_schema(self):
        """Test valid JSON against schema."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name"],
        }
        guard = SchemaGuard.from_json_schema(schema)
        ctx = Context()

        # Test valid JSON
        valid_json = '{"name": "John", "age": 30}'
        result = guard.check(valid_json, ctx)
        self.assertEqual(result.action, "allow")

    def test_invalid_json_schema(self):
        """Test invalid JSON against schema."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name"],
        }
        guard = SchemaGuard.from_json_schema(schema)
        ctx = Context()

        # Test missing required field
        invalid_json = '{"age": 30}'
        result = guard.check(invalid_json, ctx)
        self.assertEqual(result.action, "deny")

    def test_invalid_json_format(self):
        """Test invalid JSON format."""
        schema = {"type": "object"}
        guard = SchemaGuard.from_json_schema(schema)
        ctx = Context()

        # Test malformed JSON
        result = guard.check('{"name": invalid}', ctx)
        self.assertEqual(result.action, "deny")

    def test_non_json_content(self):
        """Test non-JSON content."""
        schema = {"type": "object"}
        guard = SchemaGuard.from_json_schema(schema)
        ctx = Context()

        result = guard.check("This is not JSON", ctx)
        self.assertEqual(result.action, "deny")

    def test_array_schema(self):
        """Test array schema validation."""
        schema = {"type": "array", "items": {"type": "string"}}
        guard = SchemaGuard.from_json_schema(schema)
        ctx = Context()

        # Test valid array
        result = guard.check('["item1", "item2"]', ctx)
        self.assertEqual(result.action, "allow")

        # Test invalid array
        result = guard.check("[1, 2, 3]", ctx)
        self.assertEqual(result.action, "deny")

    def test_empty_schema(self):
        """Test with empty schema."""
        guard = SchemaGuard.from_json_schema({})
        ctx = Context()

        # Empty schema should allow any valid JSON
        result = guard.check('{"anything": "goes"}', ctx)
        self.assertEqual(result.action, "allow")


if __name__ == "__main__":
    unittest.main()

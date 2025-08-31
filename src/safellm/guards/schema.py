"""Schema validation guards for JSON Schema and Pydantic models."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard

if TYPE_CHECKING:
    try:
        from pydantic import BaseModel
    except ImportError:
        pass


class SchemaGuard(BaseGuard):
    """Base class for schema validation guards."""

    @classmethod
    def from_json_schema(cls, schema: dict[str, Any]) -> JsonSchemaGuard:
        """Create a guard from a JSON Schema dictionary."""
        return JsonSchemaGuard(schema)

    @classmethod
    def from_model(cls, model: type[BaseModel]) -> PydanticSchemaGuard:
        """Create a guard from a Pydantic model class."""
        return PydanticSchemaGuard(model)


class JsonSchemaGuard(SchemaGuard):
    """Guard that validates data against a JSON Schema."""

    def __init__(self, schema: dict[str, Any]) -> None:
        """Initialize with a JSON Schema dictionary."""
        try:
            import jsonschema
        except ImportError as e:
            raise ImportError(
                "jsonschema is required for JsonSchemaGuard. "
                "Install with: pip install safellm[full]"
            ) from e

        self.schema = schema
        self.validator = jsonschema.Draft7Validator(schema)

    @property
    def name(self) -> str:
        return "json_schema"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Validate data against the JSON schema."""
        # If data is a string, try to parse it as JSON
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError as e:
                return Decision.deny(
                    data,
                    [f"Invalid JSON: {str(e)}"],
                    audit_id=ctx.audit_id,
                    evidence={"json_error": str(e)},
                )
        else:
            parsed_data = data

        # Validate against schema
        errors = list(self.validator.iter_errors(parsed_data))

        if errors:
            reasons = []
            error_details = []

            for error in errors:
                path = (
                    " -> ".join(str(p) for p in error.absolute_path)
                    if error.absolute_path
                    else "root"
                )
                reasons.append(f"Schema validation failed at {path}: {error.message}")
                error_details.append(
                    {
                        "path": list(error.absolute_path),
                        "message": error.message,
                        "invalid_value": error.instance,
                    }
                )

            return Decision.deny(
                data,
                reasons,
                audit_id=ctx.audit_id,
                evidence={
                    "schema_errors": error_details,
                    "error_count": len(errors),
                },
            )

        # Schema validation passed
        return Decision.allow(
            parsed_data if isinstance(data, str) else data,
            audit_id=ctx.audit_id,
            evidence={"schema_valid": True},
        )


class PydanticSchemaGuard(SchemaGuard):
    """Guard that validates data against a Pydantic model."""

    def __init__(self, model: type[BaseModel]) -> None:
        """Initialize with a Pydantic model class."""
        try:
            from pydantic import BaseModel
        except ImportError as e:
            raise ImportError(
                "pydantic is required for PydanticSchemaGuard. "
                "Install with: pip install safellm[full]"
            ) from e

        if not issubclass(model, BaseModel):
            raise TypeError("model must be a Pydantic BaseModel subclass")

        self.model = model

    @property
    def name(self) -> str:
        return "pydantic_schema"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Validate data against the Pydantic model."""
        try:
            from pydantic import ValidationError
        except ImportError as e:
            raise ImportError(
                "pydantic is required for PydanticSchemaGuard. "
                "Install with: pip install safellm[full]"
            ) from e

        # If data is a string, try to parse it as JSON
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError as e:
                return Decision.deny(
                    data,
                    [f"Invalid JSON: {str(e)}"],
                    audit_id=ctx.audit_id,
                    evidence={"json_error": str(e)},
                )
        else:
            parsed_data = data

        # Validate with Pydantic
        try:
            validated_instance = self.model.model_validate(parsed_data)

            # Return the validated data as a dict
            return Decision.allow(
                validated_instance.model_dump(),
                audit_id=ctx.audit_id,
                evidence={
                    "model_valid": True,
                    "model_name": self.model.__name__,
                },
            )

        except ValidationError as e:
            reasons = []
            error_details = []

            for error in e.errors():
                path = " -> ".join(str(p) for p in error["loc"]) if error["loc"] else "root"
                reasons.append(f"Validation failed at {path}: {error['msg']}")
                error_details.append(
                    {
                        "path": list(error["loc"]),
                        "message": error["msg"],
                        "type": error["type"],
                        "input": error.get("input"),
                    }
                )

            return Decision.deny(
                data,
                reasons,
                audit_id=ctx.audit_id,
                evidence={
                    "validation_errors": error_details,
                    "error_count": len(error_details),
                    "model_name": self.model.__name__,
                },
            )
        except Exception as e:
            # Catch any other validation errors
            return Decision.deny(
                data,
                [f"Unexpected validation error: {str(e)}"],
                audit_id=ctx.audit_id,
                evidence={
                    "unexpected_error": str(e),
                    "model_name": self.model.__name__,
                },
            )

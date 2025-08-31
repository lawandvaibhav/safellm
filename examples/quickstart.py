"""
SafeLLM Quickstart Example

This example demonstrates basic usage of the SafeLLM library for
validating and sanitizing LLM outputs.
"""

import json

from safellm import Context, Pipeline, ValidationError, guards


def main():
    """Demonstrate basic SafeLLM usage."""

    # Example 1: Basic pipeline with length and PII guards
    print("=== Example 1: Basic Pipeline ===")

    pipeline = Pipeline(
        name="content_safety_pipeline",
        steps=[
            guards.LengthGuard(max_chars=1000),
            guards.PiiRedactionGuard(mode="mask", targets=["email", "phone"]),
            guards.ProfanityGuard(action="mask"),
        ],
    )

    # Simulate LLM output with PII
    llm_output = """
    Hello! Please contact me at john.doe@email.com or call me at +1-555-123-4567.
    This is a perfectly normal message without any badword content.
    """

    try:
        decision = pipeline.validate(llm_output)

        if decision.allowed:
            print("✅ Content passed validation")
            if decision.action == "transform":
                print("🔧 Content was transformed:")
                print(f"Original length: {len(llm_output)}")
                print(f"Cleaned length: {len(decision.output)}")
                print(f"Cleaned content: {decision.output}")
            else:
                print(f"Content: {decision.output}")
        else:
            print("❌ Content was rejected:")
            print(f"Reasons: {', '.join(decision.reasons)}")

    except ValidationError as e:
        print(f"❌ Validation failed: {e}")
        print(f"Audit ID: {e.audit_id}")

    print()

    # Example 2: Schema validation
    print("=== Example 2: Schema Validation ===")

    # Define expected schema for structured output
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            }
        },
        "required": ["title", "summary"],
        "additionalProperties": False
    }

    schema_pipeline = Pipeline(
        name="structured_output_pipeline",
        steps=[
            guards.SchemaGuard.from_json_schema(schema),
            guards.LengthGuard(max_chars=500),
        ]
    )

    # Valid JSON output
    valid_output = {
        "title": "Climate Change Effects",
        "summary": "A comprehensive overview of climate change impacts globally.",
        "tags": ["climate", "environment", "science"],
        "confidence": 0.95
    }

    try:
        decision = schema_pipeline.validate(valid_output)
        print("✅ Valid JSON structure passed validation")
        print(f"Validated data: {json.dumps(decision.output, indent=2)}")
    except ValidationError as e:
        print(f"❌ Schema validation failed: {e}")

    print()

    # Invalid JSON output
    invalid_output = {
        "title": "Climate Change Effects",
        # Missing required "summary" field
        "confidence": 1.5,  # Invalid: > 1.0
        "extra_field": "not allowed"  # additionalProperties: false
    }

    try:
        decision = schema_pipeline.validate(invalid_output)
        print("✅ Validation passed (unexpected)")
    except ValidationError as e:
        print("❌ Invalid JSON correctly rejected:")
        print(f"Reasons: {', '.join(e.reasons)}")

    print()

    # Example 3: Custom context and async usage
    print("=== Example 3: Custom Context ===")

    async def async_example():
        """Demonstrate async usage with custom context."""

        pipeline = Pipeline(
            name="async_pipeline",
            steps=[
                guards.SecretMaskGuard(),
                guards.HtmlSanitizerGuard(policy="strict"),
            ]
        )

        # Create custom context
        ctx = Context(
            model="gpt-4",
            user_role="content_creator",
            purpose="blog_generation",
            metadata={"session_id": "abc123"}
        )

        content_with_secrets = """
        Here's my API key: sk_live_abcdef123456789
        And some HTML: <script>alert('xss')</script><p>Safe content</p>
        """

        decision = await pipeline.avalidate(content_with_secrets, ctx=ctx)

        print(f"Async validation completed with audit ID: {decision.audit_id}")
        if decision.action == "transform":
            print("🔧 Content was sanitized:")
            print(decision.output)
            print(f"Detected issues: {len(decision.evidence.get('detections', []))}")

    # Run async example
    import asyncio
    asyncio.run(async_example())

    # Example 4: Pipeline composition and error handling
    print("\n=== Example 4: Error Handling ===")

    strict_pipeline = Pipeline(
        name="strict_validation",
        steps=[
            guards.LengthGuard(max_chars=50),  # Very strict limit
            guards.ProfanityGuard(action="block"),  # Block any profanity
        ],
        fail_fast=True  # Stop at first failure
    )

    test_cases = [
        "Short and clean text",
        "This text is definitely way too long for our strict character limit policy",
        "This contains a badword which should be blocked"
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest case {i}: '{test_case[:30]}...'")
        try:
            decision = strict_pipeline.validate(test_case)
            if decision.allowed:
                print("✅ Passed all validations")
            else:
                print(f"❌ Rejected: {', '.join(decision.reasons)}")
        except ValidationError as e:
            print(f"❌ Validation error: {e}")


if __name__ == "__main__":
    main()

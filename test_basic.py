#!/usr/bin/env python3
"""
Simple test script to verify SafeLLM functionality.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from safellm import Context, Pipeline, ValidationError, guards


def test_basic_functionality():
    """Test basic SafeLLM functionality."""
    print("🧪 Testing SafeLLM Basic Functionality\n")

    # Test 1: Length validation
    print("Test 1: Length Validation")
    length_guard = guards.LengthGuard(max_chars=20)
    pipeline = Pipeline("length_test", [length_guard])

    # Should pass
    decision = pipeline.validate("Short text")
    print(f"✅ Short text: {decision.allowed}")

    # Should fail
    decision = pipeline.validate("This text is way too long and should fail")
    print(f"❌ Long text: {decision.allowed} - {decision.reasons[0] if decision.reasons else 'No reason'}")
    print()

    # Test 2: PII Redaction
    print("Test 2: PII Redaction")
    pii_guard = guards.PiiRedactionGuard(mode="mask")
    pipeline = Pipeline("pii_test", [pii_guard])

    test_text = "Email me at john.doe@example.com or call 555-123-4567"
    decision = pipeline.validate(test_text)
    print(f"Original: {test_text}")
    print(f"Redacted: {decision.output}")
    print(f"Detections: {len(decision.evidence.get('detections', []))}")
    print()

    # Test 3: Multi-guard pipeline
    print("Test 3: Multi-Guard Pipeline")
    pipeline = Pipeline("multi_test", [
        guards.LengthGuard(max_chars=100),
        guards.PiiRedactionGuard(mode="mask"),
        guards.ProfanityGuard(action="mask"),
    ])

    test_text = "Contact john.doe@example.com - no badword here!"
    decision = pipeline.validate(test_text)
    print(f"Multi-guard result: {decision.action}")
    print(f"Output: {decision.output}")
    print()

    # Test 4: Context usage
    print("Test 4: Context Usage")
    ctx = Context(model="gpt-4", user_role="admin", purpose="testing")
    decision = pipeline.validate("Test with context", ctx=ctx)
    print(f"Context audit ID: {decision.audit_id}")
    print()

    # Test 5: Error handling
    print("Test 5: Error Handling")
    strict_pipeline = Pipeline("strict", [guards.LengthGuard(max_chars=5)])

    try:
        decision = strict_pipeline.validate("This text is too long")
        if not decision.allowed:
            raise ValidationError(decision)
    except ValidationError as e:
        print(f"✅ Caught validation error: {e}")
        print(f"Audit ID: {e.audit_id}")

    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    test_basic_functionality()

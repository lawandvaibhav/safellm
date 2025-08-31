#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')

from safellm.guards.business import BusinessRulesGuard
from safellm.context import Context

# Test the same configuration as in the failing test
rules = [
    {
        "id": "min_length",
        "name": "Minimum Length",
        "type": "length",
        "config": {
            "min_length": 3,
        }
    },
    {
        "id": "no_test",
        "name": "No Test Word",
        "type": "pattern",
        "config": {
            "pattern": r"\btest\b",
            "match_required": False
        }
    }
]

guard = BusinessRulesGuard(rules=rules)
ctx = Context()

print(f"Guard action setting: {guard.action}")
print(f"Guard require_all setting: {guard.require_all}")

# Test with "test data" - should fail the pattern rule
result = guard.check("test data", ctx)
print(f"Result for 'test data': {result.action}")
print(f"Result evidence: {result.evidence}")

# Test with "Hello World" - should pass both rules  
result2 = guard.check("Hello World", ctx)
print(f"Result for 'Hello World': {result2.action}")
print(f"Result evidence: {result2.evidence}")

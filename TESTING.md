# SafeLLM Testing Documentation

## Overview

SafeLLM maintains **75% test coverage** across 1,726 lines of code with a comprehensive test suite designed to ensure reliability, safety, and correctness of all guard implementations and pipeline operations.

## Test Statistics

- **Total Tests**: 75 comprehensive test cases
- **Overall Coverage**: 75% (432 lines uncovered out of 1,726 total)
- **Test Files**: 6 specialized test modules
- **Guard Types Tested**: 16+ production guards with real-world scenarios

## Coverage by Module

### Perfect Coverage (100%)
- `src/safellm/__init__.py` - Core module initialization
- `src/safellm/context.py` - Context management for audit trails
- `src/safellm/decisions.py` - Decision logic and result structures
- `src/safellm/guards/__init__.py` - Guard module initialization
- `src/safellm/guards/length.py` - Length validation guard
- `src/safellm/utils/__init__.py` - Utility module initialization

### Excellent Coverage (90%+)
- `src/safellm/guards/profanity.py` - **95%** - Profanity detection and filtering
- `src/safellm/guards/language.py` - **94%** - Language detection and validation
- `src/safellm/guards/toxicity.py` - **91%** - Toxicity analysis and prevention

### Good Coverage (80%+)
- `src/safellm/utils/patterns.py` - **89%** - Utility pattern matching functions
- `src/safellm/guards/html.py` - **85%** - HTML sanitization and XSS prevention
- `src/safellm/pipeline.py` - **84%** - Validation pipeline orchestration
- `src/safellm/guards/injection.py` - **81%** - Prompt injection detection
- `src/safellm/guards/pii.py` - **81%** - PII detection and redaction

### Moderate Coverage (60-79%)
- `src/safellm/guards/similarity.py` - **74%** - Content similarity detection
- `src/safellm/guards/privacy.py` - **71%** - Privacy compliance enforcement
- `src/safellm/guards/secrets.py` - **68%** - Secret detection and masking
- `src/safellm/guards/business.py` - **61%** - Business rules validation
- `src/safellm/guard.py` - **59%** - Base guard implementation

### Areas for Improvement (50-59%)
- `src/safellm/guards/format.py` - **53%** - Format validation and transformation
- `src/safellm/guards/schema.py` - **47%** - JSON Schema validation

## Test Suite Structure

### Core Test Files

#### 1. `tests/test_comprehensive_coverage.py`
- **Purpose**: Core guard functionality testing
- **Coverage**: HTML sanitization, length validation, PII redaction
- **Tests**: 3 comprehensive test cases

#### 2. `tests/test_extended_guards.py` 
- **Purpose**: Advanced guard features and async support
- **Coverage**: All guard types with real-world scenarios
- **Tests**: 17 comprehensive test cases
- **Features**: Async validation, evidence collection, custom validators

#### 3. `tests/test_low_coverage_comprehensive.py`
- **Purpose**: Targeted testing for lowest coverage modules
- **Coverage**: Business rules, format, privacy, schema, similarity guards
- **Tests**: 11 specialized test cases
- **Focus**: Proper interface testing and edge cases

#### 4. `tests/test_specific_coverage.py`
- **Purpose**: Pipeline behavior and edge case testing
- **Coverage**: HTML guard policies, length constraints, pipeline error handling
- **Tests**: 20 detailed test cases
- **Features**: Error handling, fail-fast behavior, async operations

#### 5. `tests/test_edge_improvements.py`
- **Purpose**: Edge case and utility function testing
- **Coverage**: HTML edge cases, PII patterns, utility functions
- **Tests**: 5 edge case scenarios

#### 6. `tests/test_final_coverage.py`
- **Purpose**: Final coverage improvements and integration testing
- **Coverage**: Guard integration, context handling, comprehensive workflows
- **Tests**: 10 integration test cases

#### 7. `tests/unit/test_decisions.py`
- **Purpose**: Core decision logic testing
- **Coverage**: Allow, deny, retry, transform decisions
- **Tests**: 5 unit tests for decision types

## Guard Testing Coverage

### Content Safety Guards
- **ProfanityGuard** (95%): Basic filtering, custom word lists, different actions
- **ToxicityGuard** (91%): Toxicity detection, threshold configuration, async support
- **LanguageGuard** (94%): Language detection, allowed languages, confidence thresholds

### Data Protection Guards
- **PiiRedactionGuard** (81%): Email, phone, SSN, credit card detection and masking
- **SecretMaskGuard** (68%): API key, token, password detection across multiple patterns
- **PrivacyComplianceGuard** (71%): GDPR, CCPA framework compliance

### Format & Structure Guards
- **LengthGuard** (100%): Character limits, token limits, combined constraints
- **FormatGuard** (53%): Email validation, JSON validation, custom patterns
- **JsonSchemaGuard** (47%): Schema validation, error handling, factory methods
- **HtmlSanitizerGuard** (85%): XSS prevention, policy enforcement, content cleaning

### Business Logic Guards
- **BusinessRulesGuard** (61%): Custom validators, rule configuration, multiple rule types
- **SimilarityGuard** (74%): Content similarity detection, threshold configuration
- **PromptInjectionGuard** (81%): Injection pattern detection, sanitization
- **RateLimitGuard** (79%): Request frequency control, time window enforcement

## Pipeline Testing

### Core Pipeline Features
- **Initialization**: Multiple configuration options and guard composition
- **Validation Flow**: Sequential guard execution with proper data transformation
- **Error Handling**: Graceful error recovery with configurable fail-fast behavior
- **Async Support**: Full async validation pipeline with proper error propagation

### Error Handling Scenarios
- **Guard Exceptions**: Proper exception handling with configurable on_error behavior
- **Fail-Fast vs Continue**: Testing both fail-fast=True and fail-fast=False scenarios
- **Transform Actions**: Proper data transformation and output handling
- **Retry Logic**: Retry action handling and pipeline continuation

### Context and Audit
- **Audit Trails**: Proper audit ID generation and evidence collection
- **Context Propagation**: Context object handling through pipeline stages
- **Evidence Collection**: Comprehensive evidence gathering from all guards

## Running Tests

### Full Test Suite
```bash
# Run all 75 tests
python -m unittest discover tests -v

# Generate coverage report
python -m coverage run -m unittest discover tests
python -m coverage report
python -m coverage html  # Generate HTML report
```

### Specific Test Categories
```bash
# Core functionality
python -m unittest tests.test_comprehensive_coverage -v

# Extended guard features
python -m unittest tests.test_extended_guards -v

# Low coverage improvements
python -m unittest tests.test_low_coverage_comprehensive -v

# Pipeline and edge cases
python -m unittest tests.test_specific_coverage -v

# Edge case improvements
python -m unittest tests.test_edge_improvements -v

# Final integration tests
python -m unittest tests.test_final_coverage -v

# Unit tests
python -m unittest tests.unit.test_decisions -v
```

### Individual Guard Testing
```bash
# Test specific guards
python -m unittest tests.test_extended_guards.TestExtendedGuards.test_profanity_guard -v
python -m unittest tests.test_extended_guards.TestExtendedGuards.test_pii_redaction_guard -v
python -m unittest tests.test_extended_guards.TestExtendedGuards.test_html_sanitizer_guard -v
```

## Test Quality Standards

### Interface Testing
- **Proper Parameter Structures**: All guards tested with correct parameter formats
- **Error Handling**: Invalid parameters and edge cases properly handled
- **Return Values**: Correct decision types and evidence collection

### Real-World Scenarios
- **Actual Content**: Tests use realistic content examples, not just toy data
- **Multiple Patterns**: Each guard tested with various input patterns
- **Edge Cases**: Boundary conditions and unusual inputs covered

### Async Support
- **Async Guards**: All guards support async operation where applicable
- **Pipeline Async**: Full pipeline async validation tested
- **Error Propagation**: Async error handling properly implemented

## Future Testing Goals

### Version 0.2.x Target: 85% Coverage
- Improve format guard coverage (currently 53%)
- Enhance schema guard testing (currently 47%)
- Add more business rules scenarios
- Expand utils pattern coverage

### Version 1.0.0 Target: 90%+ Coverage
- Property-based testing framework
- Performance testing suite
- Load testing for production scenarios
- Comprehensive integration testing

## Contributing to Tests

When adding new features or guards:

1. **Add Unit Tests**: Test individual guard functionality
2. **Add Integration Tests**: Test guards within pipeline context
3. **Test Error Cases**: Verify proper error handling
4. **Test Async Support**: Ensure async compatibility
5. **Update Coverage**: Aim to maintain or improve overall coverage percentage

### Test Naming Conventions
- `test_{guard_name}_{scenario}`: For specific guard testing
- `test_{component}_comprehensive`: For comprehensive feature testing
- `test_{component}_edge_cases`: For boundary condition testing
- `test_{component}_async`: For async-specific testing

### Required Test Elements
- **Docstring**: Clear description of what the test validates
- **Context Setup**: Proper Context object initialization where needed
- **Assertions**: Verify both positive and negative cases
- **Evidence Checking**: Validate evidence collection when applicable
- **Error Testing**: Test invalid inputs and error conditions

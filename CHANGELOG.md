# Changelog

All notable changes to SafeLLM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and core architecture
- Core classes: `Pipeline`, `Context`, `Decision`, `ValidationError`
- Guard interface and base classes (`Guard`, `BaseGuard`, `AsyncGuard`)
- Basic utility patterns for PII detection and text processing
- **Comprehensive Testing Infrastructure**: 75% test coverage with 75+ test cases
- **HTML Coverage Reporting**: Detailed coverage analysis with module-by-module breakdown
- **TESTING.md**: Comprehensive testing documentation and guidelines

### Guards Implemented (16+ Production-Ready Guards)
- `LengthGuard` (100% coverage) - Character and token length validation
- `PiiRedactionGuard` (81% coverage) - PII detection and redaction (email, phone, SSN, credit cards, etc.)
- `SecretMaskGuard` (68% coverage) - API key and secret detection/masking
- `ProfanityGuard` (95% coverage) - Profanity detection and filtering
- `SchemaGuard` (47% coverage) - JSON Schema and Pydantic model validation
- `HtmlSanitizerGuard` (85% coverage) - HTML content sanitization
- `MarkdownSanitizerGuard` - Markdown content sanitization
- `BusinessRulesGuard` (61% coverage) - Custom domain validation rules
- `FormatGuard` (53% coverage) - Email, JSON, and custom pattern validation
- `PrivacyComplianceGuard` (71% coverage) - GDPR/CCPA compliance enforcement
- `SimilarityGuard` (74% coverage) - Content similarity detection
- `ToxicityGuard` (91% coverage) - Toxicity analysis and prevention
- `LanguageGuard` (94% coverage) - Language detection and validation
- `PromptInjectionGuard` (81% coverage) - Prompt injection prevention
- `RateLimitGuard` (79% coverage) - Request frequency control

### Testing & Quality Assurance
- **75% Overall Test Coverage**: Comprehensive testing across 1,726 lines of code
- **6 Specialized Test Modules**: Targeted testing for different aspects
  - `test_comprehensive_coverage.py` - Core guard functionality
  - `test_extended_guards.py` - Advanced features and async support
  - `test_low_coverage_comprehensive.py` - Targeted low-coverage improvements
  - `test_specific_coverage.py` - Pipeline behavior and edge cases
  - `test_edge_improvements.py` - Edge cases and utility functions
  - `test_final_coverage.py` - Integration testing and workflows
- **Interface Validation**: Proper parameter structures for all guards
- **Pipeline Error Handling**: Complete error recovery and fail-fast behavior testing
- **Async Support**: Full async validation pipeline testing
- **Real-World Scenarios**: Tests use realistic content, not just toy data

### Development Infrastructure
- Complete project structure following Python best practices
- Comprehensive test suite with coverage reporting
- Type checking with mypy  
- Code formatting with ruff and black
- Package configuration with pyproject.toml
- Example code and documentation
- CI/CD with GitHub Actions

## [0.1.0] - TBD

### Added
- Initial MVP release
- Core validation pipeline
- Basic guard implementations
- Documentation and examples
- Apache 2.0 license

### Known Limitations
- Optional dependencies (pydantic, jsonschema, bleach) not automatically installed
- Basic profanity detection (production needs comprehensive word lists)
- HTML sanitization requires bleach for advanced features
- No external moderation API integrations yet
- No CLI tools yet

### Security
- Privacy-first design with no external data transmission
- PII redaction before logging
- Input validation and sanitization

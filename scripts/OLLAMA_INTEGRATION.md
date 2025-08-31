# SafeLLM + Ollama Integration Scripts

This directory contains scripts to test and demonstrate SafeLLM's guardrails using Ollama for local AI model inference.

## Scripts Overview

### 1. `test_with_ollama_simple.py` (Recommended)
A lightweight script that tests SafeLLM guardrails with Ollama using only standard library dependencies.

**Features:**
- ✅ No additional dependencies required
- ✅ Simple synchronous execution
- ✅ Comprehensive test coverage
- ✅ Real-world integration scenarios

**Usage:**
```bash
# Test with default model
python scripts/test_with_ollama_simple.py

# Test with specific model
python scripts/test_with_ollama_simple.py --model phi3:latest

# Test with custom Ollama host
python scripts/test_with_ollama_simple.py --host http://192.168.1.100:11434
```

### 2. `test_with_ollama.py` (Advanced)
A full-featured async script with advanced testing capabilities.

**Features:**
- 🔄 Async/await support for concurrent testing
- 📊 Detailed timing and performance metrics
- 🎯 Scenario-based testing (basic, security, safety, integration)
- 📈 Advanced reporting and analysis

**Requirements:**
```bash
pip install aiohttp  # or pip install -e .[dev]
```

**Usage:**
```bash
# Run all test scenarios
python scripts/test_with_ollama.py

# Run specific scenarios
python scripts/test_with_ollama.py --scenarios basic,security

# Fast testing (skip slower checks)
python scripts/test_with_ollama.py --scenarios basic
```

## Prerequisites

### 1. Ollama Installation
Install Ollama from [ollama.ai](https://ollama.ai) and start the service:

```bash
# Start Ollama server
ollama serve

# Pull a model (choose one)
ollama pull llama3.2:latest    # 2.0GB - Good balance
ollama pull phi3:latest        # 2.2GB - Fast and efficient  
ollama pull gemma2:2b          # 1.6GB - Smallest option
ollama pull qwen2.5:7b         # 4.1GB - High quality
```

### 2. SafeLLM Installation
```bash
# Install SafeLLM with all dependencies
pip install -e .[dev,full]
```

### 3. Verify Setup
```bash
# Check Ollama is running
ollama list

# Check SafeLLM imports
python -c "import safellm; print('SafeLLM ready!')"
```

## What Gets Tested

The scripts test SafeLLM's complete guardrail suite:

### 🛡️ **Security Guards**
- **Prompt Injection** - Blocks attempts to override system instructions
- **Secret Detection** - Masks API keys, tokens, and passwords
- **HTML Sanitization** - Removes malicious scripts and unsafe HTML

### 🔒 **Privacy Guards**  
- **PII Redaction** - Masks emails, phone numbers, SSNs
- **Data Protection** - Configurable masking vs removal policies

### 📏 **Content Guards**
- **Length Limits** - Enforces character and token boundaries
- **Language Detection** - Validates content language requirements
- **Profanity Filtering** - Detects and handles offensive content

### 🔄 **Integration Testing**
- **Real-world Scenarios** - Email generation with protection
- **Pipeline Composition** - Multiple guards working together
- **Error Handling** - Graceful degradation and recovery

## Expected Results

### ✅ **Healthy System (80%+ pass rate)**
```
🎉 EXCELLENT: 7/8 tests passed (87.5%)
✅ SafeLLM + Ollama integration is working great!
   Your guardrails are protecting AI-generated content.
```

### ⚠️ **Needs Attention (60-80% pass rate)**
```
👍 GOOD: 5/8 tests passed (62.5%)
⚠️  Most features are working. Some edge cases may need attention.
```

### ❌ **Issues Detected (<60% pass rate)**
```
⚠️ NEEDS WORK: 3/8 tests passed (37.5%)
❌ Several issues detected. Check your setup.
```

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama service
ollama serve

# Check available models
ollama list
```

### SafeLLM Import Errors
```bash
# Reinstall with full dependencies
pip install -e .[dev,full]

# Test imports
python -c "from safellm import Pipeline; print('OK')"
```

### Model Performance Issues
```bash
# Use smaller/faster models for testing
python scripts/test_with_ollama_simple.py --model phi3:latest
python scripts/test_with_ollama_simple.py --model gemma2:2b
```

### Guard Parameter Errors
The scripts use the correct SafeLLM guard interfaces:
- `PiiRedactionGuard(mode="mask")` not `action="mask"`
- `SecretMaskGuard()` has no action parameter
- `HtmlSanitizerGuard(policy="strict")` not `action="transform"`

## Integration Examples

### Basic Pipeline
```python
from safellm import Pipeline
from safellm.guards import LengthGuard, ProfanityGuard

# Create protection pipeline
pipeline = Pipeline("content_safety", [
    LengthGuard(max_chars=1000),
    ProfanityGuard(action="mask")
])

# Generate content with Ollama
ollama_response = ollama_client.generate("llama3.2", prompt)

# Protect with SafeLLM
decision = pipeline.validate(ollama_response)

if decision.allowed:
    safe_content = decision.output
else:
    print(f"Blocked: {decision.reasons}")
```

### Advanced Protection
```python
# Comprehensive protection pipeline
enterprise_pipeline = Pipeline("enterprise_safety", [
    LengthGuard(max_chars=2000),
    PiiRedactionGuard(targets=["email", "phone"], mode="mask"),
    SecretMaskGuard(),
    PromptInjectionGuard(),
    HtmlSanitizerGuard(policy="strict"),
    ProfanityGuard(action="mask")
])

# Process AI-generated content
decision = enterprise_pipeline.validate(ai_content)
```

## Performance Notes

- **Model Size vs Speed**: Smaller models (2B-3B) are faster for testing
- **Guard Performance**: Most guards process in <10ms
- **Memory Usage**: Expect 1-8GB RAM depending on model size
- **Concurrent Testing**: Async script can test multiple scenarios in parallel

## Real-World Applications

These scripts demonstrate how to:

1. **Protect User-Facing Content** - Filter AI responses before showing to users
2. **Enterprise Compliance** - Ensure PII protection and content policies  
3. **Security Hardening** - Prevent prompt injection and data leaks
4. **Quality Assurance** - Validate AI outputs meet business requirements
5. **Development Testing** - Verify guardrails during feature development

The integration shows SafeLLM's ability to seamlessly protect any AI application while preserving the utility and quality of LLM outputs.

# LLM Guardrails + Sanitizer — Enterprise-Grade Python Library (Spec v0.1)

**Codename:** `safellm`

**Tagline:** "Deterministic outputs. Safe content. Production-grade controls for AI apps."

---

## 1) Vision & Scope

### 1.1 Problem

LLM-powered apps fail in production without *strong guardrails*: outputs drift from expected schemas, leak PII/secrets, contain toxic or unsafe content, or violate domain policies. Teams repeatedly rebuild ad‑hoc validators, redactors, and policy checks across services.

### 1.2 Solution

`safellm` is a lightweight, typed, **provider-agnostic** Python library that enforces **output structure**, **content safety**, and **policy compliance** with **minimal latency** and **enterprise features** (audit logs, metrics, privacy controls, and extensibility). It works with any LLM client and any framework.

### 1.3 Non-Goals

* Not another LLM client or agent framework.
* Not a moderation model provider (we integrate with your choice).
* Not a full-featured RAG system.

---

## 2) Core Principles

* **Fail-fast determinism:** Hard guarantees that outputs are valid by the time they leave your boundary.
* **Low overhead:** Sub‑millisecond hot‑path validations; graceful async support.
* **Composable:** Opt-in modules; you only pay for what you use.
* **Provider‑agnostic:** Works with OpenAI, Anthropic, Azure, local models, etc.
* **Privacy first:** No data phones-home by default. Redact before log. Data retention controls.
* **Enterprise-ready:** Strong typing, CI, security scanning, SBOM, SemVer, clear deprecations.

---

## 3) High-Level Architecture

```
Caller (your app)
   │
   ▼
LLM Client (any)
   │             ┌──────────────────────┐
   └────────────▶│  safellm.validate() │──────────────┐
                 └──────────────────────┘              │
                         │                             │
                  ┌──────┴──────────────────────┐      │
                  │  Validation Pipeline        │      │
                  │  (ordered steps)            │      │
                  │  1. Transport parsing       │      │
                  │  2. Structure/schema        │      │
                  │  3. Policy rules            │      │
                  │  4. Redaction/sanitization  │      │
                  │  5. Safety/moderation       │      │
                  │  6. Post-process (normalize)│      │
                  └──────────┬───────────────────┘      │
                             │                          │
                    ┌────────▼────────┐          ┌──────▼──────┐
                    │ Metrics/Audit   │          │ Exceptions  │
                    │ (OTel, JSON)    │          │ & Decisions │
                    └──────────────────┘          └─────────────┘
```

**Key types:**

* `Guard`: pluggable unit that inspects and/or transforms data.
* `Pipeline`: ordered chain of Guards with shared context.
* `Decision`: allow/deny/retry/transform with rich reasons & evidence.

---

## 4) MVP Feature Set (Milestone M1)

1. **Schema Enforcement**

   * JSON Schema & Pydantic v2 validators for exact output formats.
   * Strict mode (reject on extra fields) and tolerant mode (drop extras).
2. **Content Sanitization**

   * PII redaction (email, phone, address, PAN-like patterns, credit cards, IBAN, SSN) via regex + checksum.
   * Secrets masking (API keys for common vendors, JWT shape, Access Tokens).
   * HTML/Markdown sanitization (prevent script injection; allowlisted tags).
3. **Safety Filters**

   * Profanity list + smart variants (l33t, spacing, punctuation).
   * Basic jailbreak/prompt-injection pattern checks.
   * Length, token, and character-class constraints.
4. **Policy Engine (Rules DSL)**

   * Simple YAML/JSON rule files mapping conditions → actions (block, redact, replace, warn).
5. **Telemetry & Audit**

   * Structured JSON audit events (per request) with redacted payload.
   * OpenTelemetry metrics + traces (counters, latency histograms).
6. **Sync + Async APIs**

   * `validate()` and `avalidate()` with consistent semantics.
7. **Zero-Phone-Home** by default; env gates for any opt-in feature.

---

## 5) Roadmap (M2+)

* **External Moderation Adapters:** OpenAI/Anthropic/Azure moderation, AWS Comprehend, Google SA, custom L4 guard.
* **Advanced PII Detection:** spaCy/Presidio adapters; model-based detectors.
* **Policy Decision Graphs:** rule conditions referencing model, user role, purpose.
* **Sandboxed Post-Processors:** WASM/OCI hooks for controlled transforms.
* **Cost & Token Accounting:** adapters for popular SDKs.
* **Playbooks:** ready-made pipelines for common app types (chatbot, JSON API, code-gen).
* **CLI:** local testing of policies against corpora; golden files.
* **Config Server:** optional central config resolver with checksum-based rollout.

---

## 6) Public API Design (Python)

### 6.1 Quickstart

```python
from safellm import Pipeline, guards, decisions

schema = guards.SchemaGuard.from_json_schema({
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "points": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "points"]
})

pipeline = Pipeline(
    name="blog_summary_pipeline",
    steps=[
        guards.LengthGuard(max_chars=5000),
        guards.PiiRedactionGuard(mode="mask"),
        schema,
        guards.ProfanityGuard(action="block"),
    ],
)

# After you call your LLM client and get `output_text` or `output_json`:
decision = pipeline.validate(output)

if decision.allowed:
    safe_output = decision.output
else:
    # handle: log, show reason, or retry prompt
    raise decisions.ValidationError(decision)
```

### 6.2 Core Classes

```python
class Decision(NamedTuple):
    allowed: bool
    action: Literal["allow", "deny", "transform", "retry"]
    reasons: list[str]
    evidence: dict[str, Any]  # e.g., offending spans, rule ids
    output: Any  # original or transformed
    audit_id: str  # correlates with logs/traces

class Guard(Protocol):
    name: str
    async def acheck(self, data: Any, ctx: Context) -> Decision: ...
    def check(self, data: Any, ctx: Context) -> Decision: ...

class Pipeline:
    def __init__(self, name: str, steps: Sequence[Guard], *, fail_fast: bool = True, on_error: str = "deny") -> None: ...
    def validate(self, data: Any, *, ctx: Context | None = None) -> Decision: ...
    async def avalidate(self, data: Any, *, ctx: Context | None = None) -> Decision: ...
```

### 6.3 Built-in Guards (MVP)

* `LengthGuard(min_chars: int | None = None, max_chars: int | None = None, max_tokens: int | None = None)`
* `SchemaGuard.from_json_schema(schema: dict)`
* `SchemaGuard.from_model(model: type[pydantic.BaseModel])`
* `PiiRedactionGuard(mode: Literal["mask","remove"], targets: list[str] | None = None, custom_patterns: list[Pattern] | None = None)`
* `SecretMaskGuard(vendors: list[str] | None = None)`
* `ProfanityGuard(action: Literal["block","mask","flag"] = "mask")`
* `MarkdownSanitizerGuard(allowlist_tags: list[str] | None = None)`
* `HtmlSanitizerGuard(policy: str = "strict")`
* `RuleEngineGuard(rules: PolicyRules)`
* `RegexDenyGuard(patterns: list[str], reason: str)`

### 6.4 Policies DSL (YAML)

```yaml
version: 1
rules:
  - id: pii_block_finance
    when:
      any:
        - contains_pii: ["credit_card", "iban", "ssn"]
    then:
      action: deny
      message: "Financial PII detected"
  - id: profanity_mask
    when:
      any:
        - contains_profanity: true
    then:
      action: transform
      transform: mask_profanity
```

### 6.5 Error Model

```python
class ValidationError(Exception):
    def __init__(self, decision: Decision):
        self.decision = decision
        super().__init__("; ".join(decision.reasons))
```

---

## 7) Performance & Reliability Targets

* Hot-path sync validation (regex, schema) **p50 < 1 ms**, **p95 < 5 ms** for 2 KB payloads on modern CPUs.
* Async adapters amortize network calls; no background threads by default.
* Deterministic results across runs; optional `seed` context for sampling guards.
* Bounded memory; streaming-friendly interfaces planned (M2).

---

## 8) Security & Privacy Design

* **Default-deny philosophy** for unknown rule outcomes.
* **Data minimization:**

  * Redact before audit; never store raw secrets.
  * Configurable field-level retention windows.
* **Supply chain:**

  * Pinned deps, `uv`/`pip-tools` lock, Dependabot.
  * SBOM (CycloneDX), sigstore attestations (M2).
* **Secure coding:**

  * `ruff`/`mypy`/`bandit` gates in CI.
  * No dynamic `eval`; sandbox transforms only.
* **Compliance aids:** GDPR/CCPA data subject erase helpers (delete audit by `audit_id`).

---

## 9) Packaging & Compatibility

* Python **3.9 – 3.13**.
* Pure-Python; optional extras: `pydantic`, `jsonschema`, `bleach`, `presidio`, `opentelemetry`.
* Install: `pip install safellm[full]`.
* Semantic Versioning **MAJOR.MINOR.PATCH**.

---

## 10) Repository Structure

```
safellm/
  ├─ src/safellm/
  │   ├─ __init__.py
  │   ├─ pipeline.py
  │   ├─ decisions.py
  │   ├─ context.py
  │   ├─ guards/
  │   │   ├─ __init__.py
  │   │   ├─ schema.py
  │   │   ├─ length.py
  │   │   ├─ pii.py
  │   │   ├─ secrets.py
  │   │   ├─ profanity.py
  │   │   ├─ html.py
  │   │   └─ rules.py
  │   ├─ policies/
  │   │   └─ dsl.py
  │   ├─ telemetry/
  │   │   ├─ audit.py
  │   │   └─ metrics.py
  │   └─ utils/
  │       ├─ patterns.py
  │       └─ text.py
  ├─ tests/
  │   ├─ unit/
  │   ├─ property/
  │   ├─ perf/
  │   └─ fixtures/
  ├─ examples/
  │   ├─ quickstart.ipynb
  │   ├─ fastapi_middleware.py
  │   └─ cli_demo.py
  ├─ pyproject.toml
  ├─ README.md
  ├─ LICENSE (Apache-2.0)
  ├─ CHANGELOG.md
  ├─ SECURITY.md
  ├─ CODE_OF_CONDUCT.md
  ├─ CONTRIBUTING.md
  └─ .github/
      ├─ workflows/
      │   ├─ ci.yml
      │   ├─ release.yml
      │   └─ codeql.yml
      └─ ISSUE_TEMPLATE.md
```

---

## 11) Coding Standards

* **Style:** `ruff` (pep8/flake8), `black`, `isort`.
* **Typing:** `mypy --strict` (typed public API, `from __future__ import annotations`).
* **Docs:** `mkdocs-material` + `pdocs` API docs, examples tested via `doctest`.
* **Commits:** Conventional Commits; PR template with checklist.

---

## 12) CI/CD & Quality Gates

* Matrix: OS (ubuntu/mac/windows), Python 3.9–3.13.
* Steps: lint → typecheck → unit → property (Hypothesis) → perf smoke → pkg build → tests on built wheel.
* Security: `pip-audit`, `bandit`, CodeQL.
* Coverage: `pytest --cov` ≥ **90%** lines, gate on diff coverage.
* Release: tag on `v*` → build with `pdm build`/`hatch` → publish to PyPI (trusted publisher) → create GitHub Release notes from CHANGELOG.

---

## 13) Testing Strategy

* **Unit tests** for every guard (positive/negative).
* **Property-based tests** (Hypothesis) for regex resilience, round-trip sanitation.
* **Golden-file tests** for policy DSL decisions.
* **Fuzz tests** for HTML/Markdown sanitizers.
* **Performance tests** with fixed corpora; assert p50/p95.
* **Thread/async safety tests**.

---

## 14) Example Integrations

### 14.1 FastAPI Middleware (example)

```python
from fastapi import FastAPI, Request
from safellm import Pipeline, guards

app = FastAPI()

outbound_pipeline = Pipeline(
    name="chat_outbound",
    steps=[
        guards.PiiRedactionGuard(mode="mask"),
        guards.ProfanityGuard(action="block"),
    ],
)

@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    user_msg = body["message"]

    # call your LLM here → llm_reply
    llm_reply = await call_llm(user_msg)

    decision = await outbound_pipeline.avalidate(llm_reply)
    if not decision.allowed:
        return {"error": decision.reasons, "audit_id": decision.audit_id}
    return {"reply": decision.output, "audit_id": decision.audit_id}
```

### 14.2 JSON Schema enforcement with Pydantic

```python
from pydantic import BaseModel
from safellm import Pipeline, guards

class Answer(BaseModel):
    title: str
    bullets: list[str]

pipeline = Pipeline("json", [guards.SchemaGuard.from_model(Answer)])

out = llm_output_json  # your parsed JSON
decision = pipeline.validate(out)
print(decision.output)  # instance of dict (or normalized)
```

### 14.3 Policies DSL

```python
from safellm import Pipeline, guards
from safellm.policies.dsl import load_rules

rules = load_rules("policies.yml")
pipeline = Pipeline("policy", [guards.RuleEngineGuard(rules)])

result = pipeline.validate("my text with email john@doe.com")
```

---

## 15) Data Redaction & Detection Details

* **PII patterns (MVP):**

  * Emails (RFC 5322 simplified), phone numbers (E.164 & common), IP addresses (v4/v6), postal codes (US/EU/IN), credit cards (Visa/Master/Amex/Discover) with **Luhn** check, SSN-like, PAN-like (India), IBAN.
* **Secrets:** common API key formats (AWS-style, GCP SA key JSON fields, Azure, GitHub/GitLab tokens, Slack, Stripe, Twilio), JWT header.payload.signature structure.
* **Masking style:** `abc@***.com`, `+91-98******23`, `**** **** **** 1234`, full token → `sk_live_************abcd`.
* **Span reporting:** every redaction records start/end indices + category.

---

## 16) Extensibility Hooks

* `@register_guard` decorator to add custom guards.
* `Context` object holds request metadata (model, user role, purpose, trace ids, seed).
* `Transform` plugins: function registry `Registry[Callable[[Any, Context], Any]]` referenced by policy DSL.
* `Adapter` interface for external moderation providers.

---

## 17) Observability

* **Audit events:** one per pipeline run (start, per-guard, end).
* **Metrics:**

  * `safellm.guards.duration{guard=..., outcome=...}` histogram
  * `safellm.decisions.total{action=...}` counter
  * `safellm.violations{type=...}` counter
* **Tracing:** spans per guard with evidence sizes (redacted).
* **Sampling:** configurable rate for heavy evidence capture.

---

## 18) Configuration

* Runtime flags via env (all optional):

  * `SAFELLM_TELEMETRY=off|basic|otlp`
  * `SAFELLM_REDACTION_STYLE=mask|remove`
  * `SAFELLM_DEFAULT_DENY=true|false`
* File-based config: `pyproject.toml` section `[tool.safellm]` for defaults.

---

## 19) Documentation Plan

* **README:** positioning, quickstart, badges, link to docs.
* **Docs site:** concepts → tutorials → API → cookbook → FAQ → security.
* **Versioned docs** with mkdocs; example notebooks; copy-paste snippets.

---

## 20) Governance & Community

* **License:** Apache-2.0.
* **CoC:** Contributor Covenant.
* **Security policy:** `SECURITY.md` with PGP/`security@` contact, 90-day embargo.
* **Roadmap board & good-first-issues**.

---

## 21) Sample `pyproject.toml`

```toml
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "safellm"
version = "0.1.0"
description = "Enterprise-grade guardrails and sanitization for LLM apps"
readme = "README.md"
authors = [{ name = "Your Name", email = "you@example.com" }]
license = { text = "Apache-2.0" }
requires-python = ">=3.9"
dependencies = [
  "typing-extensions>=4.9",
  "jsonschema>=4.21; extra == 'full'",
  "pydantic>=2.6; extra == 'full'",
  "bleach>=6.1; extra == 'full'",
  "opentelemetry-api>=1.25; extra == 'otel'",
]

[project.optional-dependencies]
full = ["jsonschema>=4.21", "pydantic>=2.6", "bleach>=6.1"]
otel = ["opentelemetry-api>=1.25", "opentelemetry-sdk>=1.25"]

[tool.ruff]
line-length = 100

[tool.mypy]
strict = true

[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-q --cov=safellm --cov-report=term-missing"
```

---

## 22) Example Guard Implementations (Skeletons)

```python
# src/safellm/guards/length.py
from __future__ import annotations
from typing import Any
from ..decisions import Decision

class LengthGuard:
    name = "length"

    def __init__(self, *, min_chars: int | None = None, max_chars: int | None = None):
        self.min = min_chars
        self.max = max_chars

    def check(self, data: Any, ctx) -> Decision:
        s = data if isinstance(data, str) else str(data)
        n = len(s)
        reasons = []
        if self.min is not None and n < self.min:
            reasons.append(f"min_chars:{self.min} < {n}")
        if self.max is not None and n > self.max:
            reasons.append(f"max_chars:{self.max} < {n}")
        if reasons:
            return Decision(False, "deny", reasons, {}, data, ctx.audit_id)
        return Decision(True, "allow", [], {}, data, ctx.audit_id)
```

```python
# src/safellm/guards/schema.py
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ValidationError as PydanticVE
from ..decisions import Decision

class SchemaGuard:
    name = "schema"

    @classmethod
    def from_model(cls, model: type[BaseModel]) -> "SchemaGuard":
        return _PydanticSchemaGuard(model)

class _PydanticSchemaGuard(SchemaGuard):
    def __init__(self, model: type[BaseModel]):
        self.model = model

    def check(self, data: Any, ctx) -> Decision:
        try:
            self.model.model_validate(data)
            return Decision(True, "allow", [], {}, data, ctx.audit_id)
        except PydanticVE as e:
            return Decision(False, "deny", ["schema_invalid"], {"errors": e.errors()}, data, ctx.audit_id)
```

---

## 23) Enterprise Readiness Checklist

* [ ] ≥ 90% test coverage & diff coverage gate
* [ ] CI: Linux/Mac/Win + Python 3.9–3.13
* [ ] Type-stub completeness for public API
* [ ] SECURITY.md with contact & SLA
* [ ] CODEOWNERS & mandatory reviews
* [ ] Reproducible builds & signed releases
* [ ] SBOM generated on release
* [ ] Backwards-compat policy & deprecation guide

---

## 24) Rollout Plan

1. **v0.1.0 (M1):** Core pipeline, schema, PII/secrets, profanity, HTML/MD sanitizers, telemetry basics.
2. **v0.2.x:** Policy DSL + CLI + FastAPI middleware example.
3. **v0.3.x:** External moderation adapters + advanced PII (Presidio adapter) + cost tracking.
4. **v1.0.0:** Stability guarantees, performance hardening, signed releases, docs complete.

---

## 25) "Agent-Ready" Task List (Generate Code From This)

* Create repo skeleton per **Section 10**.
* Implement **Decision**, **Guard protocol**, **Pipeline**.
* Add MVP guards in **Section 6.3**.
* Implement regex & checksum utilities in `utils/patterns.py`.
* Add audit + metrics shims in `telemetry/` (no-op if disabled).
* Wire env config defaults (Section 18).
* Write unit + property tests (Section 13) for each guard.
* Set up CI/CD workflows (Section 12) and pre-commit hooks.
* Provide **examples** from Section 14.
* Publish `0.1.0` to TestPyPI, then PyPI.

---

## 26) Naming & Branding

* Package: `safellm`
* Module prefix: `safellm.*`
* Badges: PyPI version, downloads, coverage, license, type-checked, OTel-ready.

---

## 27) FAQ

* **Q:** Is this a replacement for LangChain/LLM SDKs?
  **A:** No, it’s orthogonal. Use it alongside any client.
* **Q:** Does it store my data?
  **A:** No. By default, nothing leaves your process. Telemetry is opt-in and redacted.
* **Q:** Can I add custom rules?
  **A:** Yes—custom guards and transforms + rules DSL.

---

*End of Spec v0.1*

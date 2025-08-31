"""Privacy compliance guard for GDPR, CCPA, and other regulations."""

from __future__ import annotations

import re
from typing import Any, Literal

from ..context import Context
from ..decisions import Decision
from ..guard import BaseGuard


class PrivacyComplianceGuard(BaseGuard):
    """Guard that ensures content complies with privacy regulations like GDPR, CCPA."""

    # Privacy-sensitive data patterns
    PRIVACY_PATTERNS = {
        "medical": [
            r'\b(?:diagnosed|diagnosis|treatment|medication|prescription|therapy|surgery|hospital|clinic|doctor|physician|patient)\b',
            r'\b(?:medical|health|illness|disease|condition|symptom|drug|medicine)\s+(?:record|history|information|data)\b',
            r'\b(?:HIV|AIDS|cancer|diabetes|depression|anxiety|bipolar|schizophrenia|addiction)\b',
        ],
        "financial": [
            r'\b(?:income|salary|wage|earnings|debt|loan|mortgage|credit|banking|investment|account|balance)\b',
            r'\b(?:financial|economic|monetary)\s+(?:status|situation|condition|information|data|record)\b',
            r'\b(?:tax|IRS|revenue|audit|bankruptcy|foreclosure)\b',
        ],
        "biometric": [
            r'\b(?:fingerprint|facial recognition|retina|iris|voice print|DNA|genetic|biometric)\b',
            r'\b(?:scan|scanning|recognition|identification|biometric)\s+(?:data|information|system)\b',
        ],
        "location": [
            r'\b(?:home address|work address|current location|GPS|coordinates|tracking)\b',
            r'\b(?:lives at|resides at|located at|address is|can be found at)\b',
            r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)\b',
        ],
        "personal_identifiers": [
            r'\b(?:social security|SSN|driver\'s license|passport|ID number|employee ID)\b',
            r'\b(?:date of birth|DOB|age|born on|birthday)\b',
            r'\b(?:mother\'s maiden name|security question|password|PIN)\b',
        ],
        "communication": [
            r'\b(?:private message|personal email|phone conversation|text message|chat log)\b',
            r'\b(?:confidential|private|personal|sensitive)\s+(?:communication|correspondence|message)\b',
        ],
        "minors": [
            r'\b(?:child|kid|minor|under 18|underage|juvenile|teenager|adolescent)\b.*\b(?:personal|private|sensitive)\s+(?:information|data)\b',
            r'\b(?:school|educational)\s+(?:record|information|data)\b.*\b(?:child|student|minor)\b',
        ],
    }

    # Compliance frameworks
    COMPLIANCE_RULES = {
        "gdpr": {
            "required_categories": ["medical", "biometric", "personal_identifiers"],
            "description": "General Data Protection Regulation (EU)",
        },
        "ccpa": {
            "required_categories": ["personal_identifiers", "biometric", "financial", "location"],
            "description": "California Consumer Privacy Act",
        },
        "hipaa": {
            "required_categories": ["medical"],
            "description": "Health Insurance Portability and Accountability Act",
        },
        "coppa": {
            "required_categories": ["minors"],
            "description": "Children's Online Privacy Protection Act",
        },
    }

    def __init__(
        self,
        frameworks: list[str] | None = None,
        action: Literal["block", "flag", "anonymize"] = "flag",
        sensitivity_threshold: float = 0.5,
        include_categories: list[str] | None = None,
    ) -> None:
        """Initialize the privacy compliance guard.
        
        Args:
            frameworks: List of compliance frameworks to check against
            action: What to do when privacy violations are detected
            sensitivity_threshold: Threshold for triggering privacy concerns
            include_categories: Specific privacy categories to check
        """
        self.frameworks = frameworks or ["gdpr", "ccpa"]
        self.action = action
        self.sensitivity_threshold = sensitivity_threshold
        
        # Determine which categories to check
        if include_categories:
            self.categories = set(include_categories)
        else:
            # Combine categories from all specified frameworks
            self.categories = set()
            for framework in self.frameworks:
                if framework in self.COMPLIANCE_RULES:
                    self.categories.update(self.COMPLIANCE_RULES[framework]["required_categories"])
        
        # Compile patterns for selected categories
        self.compiled_patterns = {}
        for category in self.categories:
            if category in self.PRIVACY_PATTERNS:
                self.compiled_patterns[category] = [
                    re.compile(pattern, re.IGNORECASE)
                    for pattern in self.PRIVACY_PATTERNS[category]
                ]

    @property
    def name(self) -> str:
        return "privacy_compliance"

    def check(self, data: Any, ctx: Context) -> Decision:
        """Check for privacy compliance violations."""
        if not isinstance(data, str):
            text = str(data)
        else:
            text = data

        # Detect privacy-sensitive content
        detections = self._detect_privacy_issues(text)
        sensitivity_score = self._calculate_sensitivity_score(detections)
        
        # Check against compliance frameworks
        violations = self._check_compliance_violations(detections)
        
        evidence = {
            "detections": detections,
            "sensitivity_score": sensitivity_score,
            "compliance_violations": violations,
            "frameworks_checked": self.frameworks,
            "categories_checked": list(self.categories),
        }

        if sensitivity_score >= self.sensitivity_threshold or violations:
            reasons = []
            if violations:
                reasons.append(f"Privacy compliance violations detected: {', '.join(violations)}")
            if sensitivity_score >= self.sensitivity_threshold:
                reasons.append(f"High privacy sensitivity score: {sensitivity_score:.2f}")
            
            if self.action == "block":
                return Decision.deny(
                    data,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            elif self.action == "anonymize":
                anonymized_text = self._anonymize_content(text, detections)
                reasons.append("Content anonymized for privacy compliance")
                return Decision.transform(
                    data,
                    anonymized_text,
                    reasons,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )
            else:  # flag
                return Decision.allow(
                    data,
                    audit_id=ctx.audit_id,
                    evidence=evidence,
                )

        return Decision.allow(
            data,
            audit_id=ctx.audit_id,
            evidence=evidence,
        )

    def _detect_privacy_issues(self, text: str) -> list[dict[str, Any]]:
        """Detect privacy-sensitive content in text."""
        detections = []
        
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = list(pattern.finditer(text))
                for match in matches:
                    detections.append({
                        "category": category,
                        "pattern": pattern.pattern,
                        "match": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "context": text[max(0, match.start() - 20):match.end() + 20],
                    })
        
        return detections

    def _calculate_sensitivity_score(self, detections: list[dict[str, Any]]) -> float:
        """Calculate privacy sensitivity score."""
        if not detections:
            return 0.0
        
        # Weight different categories by sensitivity
        category_weights = {
            "medical": 1.0,
            "biometric": 1.0,
            "personal_identifiers": 0.9,
            "financial": 0.8,
            "minors": 1.0,
            "location": 0.7,
            "communication": 0.6,
        }
        
        category_scores = {}
        for detection in detections:
            category = detection["category"]
            weight = category_weights.get(category, 0.5)
            
            if category not in category_scores:
                category_scores[category] = 0.0
            
            category_scores[category] = max(category_scores[category], weight)
        
        # Calculate overall score
        if not category_scores:
            return 0.0
        
        # Average of category scores with bonus for multiple categories
        base_score = sum(category_scores.values()) / len(category_scores)
        category_bonus = min(0.3, (len(category_scores) - 1) * 0.1)
        
        return min(1.0, base_score + category_bonus)

    def _check_compliance_violations(self, detections: list[dict[str, Any]]) -> list[str]:
        """Check for specific compliance framework violations."""
        violations = []
        detected_categories = set(d["category"] for d in detections)
        
        for framework in self.frameworks:
            if framework in self.COMPLIANCE_RULES:
                required_categories = self.COMPLIANCE_RULES[framework]["required_categories"]
                framework_violations = detected_categories.intersection(required_categories)
                
                if framework_violations:
                    violations.append(f"{framework.upper()} ({', '.join(framework_violations)})")
        
        return violations

    def _anonymize_content(self, text: str, detections: list[dict[str, Any]]) -> str:
        """Anonymize privacy-sensitive content."""
        # Sort detections by start position in reverse order
        sorted_detections = sorted(detections, key=lambda x: x["start"], reverse=True)
        
        result = text
        for detection in sorted_detections:
            start = detection["start"]
            end = detection["end"]
            category = detection["category"]
            
            # Create appropriate replacement
            if category == "medical":
                replacement = "[MEDICAL_INFO_REDACTED]"
            elif category == "financial":
                replacement = "[FINANCIAL_INFO_REDACTED]"
            elif category == "biometric":
                replacement = "[BIOMETRIC_DATA_REDACTED]"
            elif category == "location":
                replacement = "[LOCATION_REDACTED]"
            elif category == "personal_identifiers":
                replacement = "[PERSONAL_ID_REDACTED]"
            elif category == "communication":
                replacement = "[PRIVATE_COMMUNICATION_REDACTED]"
            elif category == "minors":
                replacement = "[MINOR_INFO_REDACTED]"
            else:
                replacement = "[PRIVACY_SENSITIVE_REDACTED]"
            
            result = result[:start] + replacement + result[end:]
        
        return result

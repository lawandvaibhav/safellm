"""Pattern utilities for PII detection and content sanitization."""

from __future__ import annotations

import re
from typing import Pattern


# Email patterns
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

# Phone number patterns (various formats)
PHONE_PATTERNS = [
    re.compile(r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),  # International
    re.compile(r'\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}'),  # US format with parentheses
    re.compile(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'),  # US format
    re.compile(r'\d{10,15}'),  # Generic long number
]

# Credit card patterns with basic validation
CREDIT_CARD_PATTERNS = [
    re.compile(r'\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # Visa
    re.compile(r'\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # MasterCard
    re.compile(r'\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b'),  # American Express
    re.compile(r'\b6011[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # Discover
]

# SSN patterns
SSN_PATTERN = re.compile(r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b')

# IP address patterns
IPV4_PATTERN = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

IPV6_PATTERN = re.compile(
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|'
    r'\b::1\b|'
    r'\b::ffff:[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b',
    re.IGNORECASE
)

# API key patterns
API_KEY_PATTERNS = [
    re.compile(r'\bsk_live_[a-zA-Z0-9]{24,}\b'),  # Stripe live keys
    re.compile(r'\bsk_test_[a-zA-Z0-9]{24,}\b'),  # Stripe test keys
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),  # AWS Access Key ID
    re.compile(r'\bAIza[0-9A-Za-z\-_]{35}\b'),  # Google API Key
    re.compile(r'\bghp_[a-zA-Z0-9]{36}\b'),  # GitHub Personal Access Token
    re.compile(r'\bgho_[a-zA-Z0-9]{36}\b'),  # GitHub OAuth Token
    re.compile(r'\bxoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+\b'),  # Slack Bot Token
    re.compile(r'\bxoxp-[0-9]+-[0-9]+-[0-9]+-[a-zA-Z0-9]+\b'),  # Slack User Token
]

# JWT pattern
JWT_PATTERN = re.compile(
    r'\beyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b'
)

# Basic password patterns (common indicators)
PASSWORD_INDICATORS = re.compile(
    r'(?i)\b(?:password|passwd|pwd|pass|secret|key|token)\s*[:=]\s*["\']?([^"\'\s]+)["\']?',
    re.IGNORECASE
)

# IBAN pattern
IBAN_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b')

# Address patterns (basic)
ADDRESS_PATTERNS = [
    re.compile(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)\b', re.IGNORECASE),
    re.compile(r'\b\d{5}(?:-\d{4})?\b'),  # US ZIP codes
]


def luhn_check(card_number: str) -> bool:
    """Validate credit card number using Luhn algorithm."""
    # Remove non-digit characters
    digits = [int(x) for x in card_number if x.isdigit()]
    
    if len(digits) < 13 or len(digits) > 19:
        return False
    
    # Apply Luhn algorithm
    checksum = 0
    is_even = False
    
    for digit in reversed(digits):
        if is_even:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
        is_even = not is_even
    
    return checksum % 10 == 0


def mask_text(text: str, start: int = 2, end: int = 2, mask_char: str = "*") -> str:
    """Mask a string, keeping start and end characters visible."""
    if len(text) <= start + end:
        return mask_char * len(text)
    
    return (
        text[:start] +
        mask_char * (len(text) - start - end) +
        text[-end:] if end > 0 else ""
    )


def mask_email(email: str) -> str:
    """Mask an email address."""
    if "@" not in email:
        return mask_text(email)
    
    local, domain = email.split("@", 1)
    if "." not in domain:
        return f"{mask_text(local, 1, 0)}@{mask_text(domain)}"
    
    domain_parts = domain.split(".")
    domain_name = domain_parts[0]
    domain_ext = ".".join(domain_parts[1:])
    
    return f"{mask_text(local, 1, 0)}@{mask_text(domain_name, 0, 0)}.{domain_ext}"


def mask_phone(phone: str) -> str:
    """Mask a phone number."""
    # Extract just digits
    digits = ''.join(c for c in phone if c.isdigit())
    
    if len(digits) >= 10:
        # Show country code and last 2-3 digits
        if len(digits) > 10:
            return f"+{digits[0]}***-***{digits[-2:]}"
        else:
            return f"***-***-{digits[-2:]}"
    else:
        return mask_text(phone, 1, 2)


def mask_credit_card(card: str) -> str:
    """Mask a credit card number."""
    # Extract just digits
    digits = ''.join(c for c in card if c.isdigit())
    
    if len(digits) >= 13:
        return f"**** **** **** {digits[-4:]}"
    else:
        return mask_text(card, 0, 4)


def mask_api_key(key: str) -> str:
    """Mask an API key."""
    if len(key) > 8:
        return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"
    else:
        return mask_text(key, 2, 2)


# Profanity word lists (basic - in production you'd want a more comprehensive list)
BASIC_PROFANITY = {
    # Add common profanity words here
    # This is a placeholder - real implementation would have comprehensive lists
    "badword", "offensive", "inappropriate"
}

# L33t speak mappings for profanity detection
LEET_MAPPINGS = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
}


def normalize_leet_speak(text: str) -> str:
    """Normalize l33t speak to regular characters."""
    result = text.lower()
    for leet, normal in LEET_MAPPINGS.items():
        result = result.replace(leet, normal)
    return result


def contains_profanity(text: str) -> bool:
    """Check if text contains profanity (basic implementation)."""
    normalized = normalize_leet_speak(text)
    # Remove punctuation and spaces for detection
    cleaned = ''.join(c for c in normalized if c.isalnum())
    
    for word in BASIC_PROFANITY:
        if word in cleaned:
            return True
    
    return False

"""Output filtering and content safety for LLM-generated text."""

import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

UNSAFE_PATTERNS = [
    (re.compile(r"\b(kill\s+yourself|suicide)\b", re.I), "[content removed]"),
    (re.compile(r"\b(stop\s+taking\s+all\s+medication)\b", re.I), "consult your physician before changing medications"),
    (re.compile(r"<script[^>]*>.*?</script>", re.I | re.S), ""),
]

DISCLAIMER = (
    "This information is for educational purposes only and does not replace "
    "professional medical advice. Always consult your healthcare provider."
)


def sanitize_string(value: str, max_length: int = 2000) -> str:
    """Remove unsafe content from a string."""
    if not value:
        return ""
    result = value[:max_length]
    for pattern, replacement in UNSAFE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result.strip()


def filter_output(text: str, add_disclaimer: bool = True) -> str:
    """Filter LLM output and optionally append medical disclaimer."""
    filtered = sanitize_string(text)
    if add_disclaimer and filtered and DISCLAIMER not in filtered:
        filtered = f"{filtered}\n\n{DISCLAIMER}"
    return filtered


def filter_patient_output(
    summary: str, advice: List[str], add_disclaimer: bool = True
) -> Dict[str, Any]:
    """Filter patient communication output."""
    return {
        "summary": filter_output(summary, add_disclaimer=add_disclaimer),
        "lifestyle_advice": [sanitize_string(a, 500) for a in advice if a],
    }

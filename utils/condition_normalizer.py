"""Backward-compatible condition normalization helpers."""

from utils.normalization import (
    CONDITION_ALIASES,
    MEDICATION_ALIASES,
    normalize_condition,
    normalize_conditions,
    normalize_medication,
    normalize_medications,
)

__all__ = [
    "CONDITION_ALIASES",
    "MEDICATION_ALIASES",
    "normalize_condition",
    "normalize_conditions",
    "normalize_medication",
    "normalize_medications",
]

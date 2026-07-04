"""Input validation and sanitization for patient data and queries."""

import logging
import re
from typing import Any, Dict, List, Tuple

from utils.normalization import normalize_conditions, normalize_medications

logger = logging.getLogger(__name__)

ALLOWED_CONDITIONS = {
    "hypertension", "dyslipidemia", "smoker", "diabetes", "ckd",
    "hyperkalemia", "bilateral_renal_artery_stenosis", "asthma",
    "gout", "pregnancy", "liver_disease", "bradycardia",
    "coronary_artery_disease", "heart_failure", "atrial_fibrillation",
}

BP_PATTERN = re.compile(r"^\d{2,3}/\d{2,3}$")
INJECTION_PATTERN = re.compile(
    r"(<script|javascript:|DROP\s+TABLE|;\s*--|\{\{|\}\})",
    re.IGNORECASE,
)


class ValidationError(Exception):
    """Raised when input fails validation."""


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Strip dangerous patterns and truncate."""
    if not isinstance(value, str):
        value = str(value)
    cleaned = INJECTION_PATTERN.sub("", value.strip())
    return cleaned[:max_length]


def validate_query(query: str) -> str:
    """Validate and sanitize clinical query."""
    if not query or not query.strip():
        raise ValidationError("Clinical query is required")

    cleaned = sanitize_string(query, max_length=1000)
    if len(cleaned) < 3:
        raise ValidationError("Query must be at least 3 characters")
    return cleaned


def sanitize_patient_payload(patient: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Validate and sanitize patient data using a single shared implementation."""
    warnings: List[str] = []

    if not patient:
        raise ValidationError("Patient data is required")

    age = patient.get("age")
    if age is None:
        raise ValidationError("Patient age is required")
    try:
        age = int(age)
    except (TypeError, ValueError):
        raise ValidationError("Patient age must be an integer")
    if not 18 <= age <= 120:
        raise ValidationError("Patient age must be between 18 and 120")

    bp = patient.get("bp", "120/80")
    if not isinstance(bp, str) or not BP_PATTERN.match(bp.strip()):
        raise ValidationError("Blood pressure must be in format SBP/DBP (e.g. 120/80)")

    ldl = patient.get("ldl", 100)
    try:
        ldl = float(ldl)
    except (TypeError, ValueError):
        raise ValidationError("LDL must be a number")
    if not 0 <= ldl <= 500:
        raise ValidationError("LDL must be between 0 and 500 mg/dL")

    raw_conditions = patient.get("conditions", [])
    if not isinstance(raw_conditions, list):
        raise ValidationError("Conditions must be a list")

    conditions = normalize_conditions(raw_conditions)
    for cond in conditions:
        if cond not in ALLOWED_CONDITIONS:
            warnings.append(f"Unknown condition '{cond}' — will attempt best-match lookup")

    medications = patient.get("medications", [])
    if medications and not isinstance(medications, list):
        raise ValidationError("Medications must be a list")
    normalized_medications = normalize_medications(medications)

    sex = patient.get("sex", "Male")
    if sex not in ("Male", "Female", "male", "female", "M", "F"):
        warnings.append(f"Unrecognized sex '{sex}', defaulting to Male")
        sex = "Male"

    cleaned = {
        "age": age,
        "bp": bp.strip(),
        "ldl": ldl,
        "conditions": conditions,
        "medications": [
            sanitize_string(str(m), 100).lower().replace(" ", "_")
            for m in normalized_medications
        ],
        "sex": sex.capitalize() if sex.lower() in ("male", "female") else sex,
    }

    if patient.get("hdl"):
        try:
            cleaned["hdl"] = float(patient["hdl"])
        except (TypeError, ValueError):
            warnings.append("Invalid HDL value ignored")

    if patient.get("total_cholesterol"):
        try:
            cleaned["total_cholesterol"] = float(patient["total_cholesterol"])
        except (TypeError, ValueError):
            warnings.append("Invalid total cholesterol value ignored")

    if patient.get("on_bp_medication") is not None:
        cleaned["on_bp_medication"] = bool(patient["on_bp_medication"])

    logger.info("Patient input validated: age=%d, conditions=%s", age, conditions)
    return cleaned, warnings


def validate_patient_input(patient: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Backward-compatible wrapper for patient sanitization."""
    return sanitize_patient_payload(patient)

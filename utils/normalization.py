"""Shared normalization helpers for conditions and medications."""

from __future__ import annotations

from typing import Iterable, List

CONDITION_ALIASES = {
    "smoking": "smoker",
    "tobacco_use": "smoker",
    "active_smoker": "smoker",
    "current_smoker": "smoker",
    "htn": "hypertension",
    "high_blood_pressure": "hypertension",
    "elevated_bp": "hypertension",
    "hyperlipidemia": "dyslipidemia",
    "high_cholesterol": "dyslipidemia",
    "elevated_ldl": "dyslipidemia",
    "dm": "diabetes",
    "diabetes_mellitus": "diabetes",
    "type_2_diabetes": "diabetes",
    "type2_diabetes": "diabetes",
    "chronic_kidney_disease": "ckd",
    "renal_disease": "ckd",
    "kidney_disease": "ckd",
    "pregnant": "pregnancy",
    "hepatic_disease": "liver_disease",
}

MEDICATION_ALIASES = {
    "lisinopril": "ace_inhibitor",
    "enalapril": "ace_inhibitor",
    "ramipril": "ace_inhibitor",
    "losartan": "arb",
    "valsartan": "arb",
    "atorvastatin": "statin",
    "simvastatin": "statin",
    "rosuvastatin": "statin",
    "metoprolol": "beta_blocker",
    "atenolol": "beta_blocker",
    "carvedilol": "beta_blocker",
    "hydrochlorothiazide": "thiazide",
    "hctz": "thiazide",
    "coumadin": "warfarin",
    "jantoven": "warfarin",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "tylenol": "acetaminophen",
}


def normalize_condition(condition: str) -> str:
    key = condition.lower().strip().replace(" ", "_").replace("-", "_")
    return CONDITION_ALIASES.get(key, key)


def normalize_conditions(conditions: Iterable[str] | None) -> List[str]:
    if not conditions:
        return []
    return list(dict.fromkeys(normalize_condition(c) for c in conditions if c))


def normalize_medication(medication: str) -> str:
    key = medication.lower().strip().replace(" ", "_").replace("-", "_")
    return MEDICATION_ALIASES.get(key, key)


def normalize_medications(medications: Iterable[str] | None) -> List[str]:
    if not medications:
        return []
    return [normalize_medication(m) for m in medications if m]

"""ASCVD-inspired cardiovascular risk calculator."""

import logging
import math
from typing import Dict, List

from utils.condition_normalizer import normalize_conditions

logger = logging.getLogger(__name__)


def _parse_systolic_bp(bp: str) -> int:
    return int(bp.split("/")[0])


def _estimate_hdl(ldl: float, total_chol: float = None) -> float:
    """Estimate HDL when not provided."""
    if total_chol:
        return max(30.0, total_chol - ldl - 50)
    return max(35.0, 100 - ldl * 0.3)


def _ascvd_10yr_risk(
    age: int,
    sex: str,
    total_chol: float,
    hdl: float,
    systolic_bp: int,
    on_bp_meds: bool,
    smoker: bool,
    diabetic: bool,
) -> float:
    """
    Simplified ASCVD Pooled Cohort Equations (2013 ACC/AHA).
    Returns 10-year ASCVD risk percentage (0-100).
    """
    is_female = sex.lower() in ("female", "f")
    ln_age = math.log(age)
    ln_tc = math.log(total_chol)
    ln_hdl = math.log(hdl)
    ln_sbp = math.log(systolic_bp)

    if is_female:
        s = (
            -29.799 * ln_age
            + 4.884 * (ln_age ** 2)
            + 13.540 * ln_tc
            + -3.114 * ln_age * ln_tc
            + -13.578 * ln_hdl
            + 3.149 * ln_age * ln_hdl
            + (2.019 if on_bp_meds else 1.957) * ln_sbp
            + (0.0 if on_bp_meds else -0.0)
            + (0.661 if smoker else 0.0)
            + (0.0 if on_bp_meds else 0.0)
            + (0.573 if diabetic else 0.0)
            - 29.18
        )
        baseline = 0.9665
    else:
        s = (
            12.344 * ln_age
            + 11.853 * ln_tc
            + -2.664 * ln_age * ln_tc
            + -7.990 * ln_hdl
            + 1.769 * ln_age * ln_hdl
            + (1.797 if on_bp_meds else 1.764) * ln_sbp
            + (0.0 if on_bp_meds else 0.0)
            + (0.658 if smoker else 0.0)
            + (0.573 if diabetic else 0.0)
            - 61.18
        )
        baseline = 0.9144

    risk = 1 - (baseline ** math.exp(s))
    return max(0.0, min(risk * 100, 100.0))


class RiskScoreCalculator:
    """
    Cardiovascular risk scoring using ASCVD Pooled Cohort Equations
    with composite fallback scoring.
    """

    def run(self, patient: dict) -> dict:
        logger.info("[RiskScoreCalculator] Calculating ASCVD risk score.")
        factors: List[str] = []

        age = int(patient.get("age", 40))
        sex = patient.get("sex", "Male")
        bp = patient.get("bp", "120/80")
        ldl = float(patient.get("ldl", 100))
        conditions = normalize_conditions(patient.get("conditions", []))

        smoker = "smoker" in conditions
        diabetic = "diabetes" in conditions
        systolic = _parse_systolic_bp(bp)
        on_bp_meds = bool(patient.get("on_bp_medication", False))

        total_chol = patient.get("total_cholesterol")
        if total_chol:
            total_chol = float(total_chol)
        else:
            total_chol = ldl + 50 + 45

        hdl = patient.get("hdl")
        if hdl:
            hdl = float(hdl)
        else:
            hdl = _estimate_hdl(ldl, total_chol)

        try:
            ascvd_risk = _ascvd_10yr_risk(
                age=age,
                sex=sex,
                total_chol=total_chol,
                hdl=hdl,
                systolic_bp=systolic,
                on_bp_meds=on_bp_meds,
                smoker=smoker,
                diabetic=diabetic,
            )
            score = round(ascvd_risk, 1)
            factors.append(f"ASCVD 10-year risk: {score}%")
        except (ValueError, OverflowError) as exc:
            logger.warning("ASCVD calculation failed: %s, using composite score", exc)
            score = self._composite_score(patient, conditions, factors)

        if age >= 65:
            factors.append(f"Age {age} (≥65 years)")
        if systolic >= 140:
            factors.append(f"Stage 2 hypertension (SBP {systolic})")
        elif systolic >= 130:
            factors.append(f"Stage 1 hypertension (SBP {systolic})")
        if ldl >= 190:
            factors.append(f"Very high LDL ({ldl} mg/dL)")
        elif ldl >= 160:
            factors.append(f"High LDL ({ldl} mg/dL)")
        elif ldl >= 130:
            factors.append(f"Borderline LDL ({ldl} mg/dL)")
        if smoker:
            factors.append("Active smoker")
        if diabetic:
            factors.append("Diabetes mellitus")
        if "ckd" in conditions:
            factors.append("Chronic kidney disease")
            score = min(score + 5, 100)

        score = min(round(score, 1), 100)

        if score < 5:
            classification = "Low"
        elif score < 7.5:
            classification = "Moderate"
        elif score < 20:
            classification = "High"
        else:
            classification = "Very High"

        return {
            "score": score,
            "classification": classification,
            "factors": factors,
            "method": "ASCVD Pooled Cohort Equations (2013 ACC/AHA)",
        }

    def _composite_score(
        self, patient: dict, conditions: list, factors: List[str]
    ) -> float:
        """Fallback composite scoring when ASCVD inputs are insufficient."""
        score = 0.0
        age = int(patient.get("age", 40))
        if age >= 65:
            score += 25
        elif age >= 55:
            score += 15

        systolic = _parse_systolic_bp(patient.get("bp", "120/80"))
        if systolic >= 160:
            score += 25
        elif systolic >= 140:
            score += 15
        elif systolic >= 130:
            score += 8

        ldl = float(patient.get("ldl", 0))
        if ldl >= 190:
            score += 20
        elif ldl >= 160:
            score += 12
        elif ldl >= 130:
            score += 6

        if "smoker" in conditions:
            score += 20
        if "diabetes" in conditions:
            score += 15
        if "ckd" in conditions:
            score += 10

        factors.append("Composite fallback scoring used")
        return min(score, 100)
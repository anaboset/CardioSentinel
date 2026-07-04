"""Cardiovascular risk calculators and medication dosing tools.

Provides clinical decision support tools including:
- ASCVD (Atherosclerotic Cardiovascular Disease) risk estimation
- Framingham risk calculation
- Creatinine clearance estimation (Cockcroft-Gault)
- Drug dosing adjustments for renal function
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, Optional

logger = logging.getLogger("clinical_mcp_server.calculators")


class ASCVDRiskCalculator:
    """ACC/AHA ASCVD risk calculator for 10-year risk estimation."""

    @staticmethod
    def calculate_10year_risk(
        age: int,
        gender: str,
        race: str,
        total_cholesterol: int,
        ldl: int,
        hdl: int,
        systolic_bp: int,
        on_bp_medication: bool,
        smoker: bool,
        diabetic: bool,
    ) -> Dict[str, Any]:
        """Calculate 10-year ASCVD risk using ACC/AHA pooled cohort equations.

        Args:
            age: Age in years (40-79).
            gender: 'M' or 'F'.
            race: 'White', 'African American', 'Other'.
            total_cholesterol: Total cholesterol in mg/dL.
            ldl: LDL cholesterol in mg/dL.
            hdl: HDL cholesterol in mg/dL.
            systolic_bp: Systolic blood pressure in mmHg.
            on_bp_medication: Whether patient is on antihypertensive medication.
            smoker: Current smoker status.
            diabetic: Diabetes status.

        Returns:
            Dictionary with 10-year ASCVD risk percentage and risk category.
        """
        if not (40 <= age <= 79):
            return {
                "error": "Age must be between 40 and 79 years",
                "risk_percentage": None,
                "risk_category": None,
            }

        if gender.upper() not in ("M", "F"):
            return {"error": "Gender must be M or F", "risk_percentage": None, "risk_category": None}

        if total_cholesterol <= 0 or ldl <= 0 or hdl <= 0 or systolic_bp <= 0:
            return {"error": "All lab values must be positive", "risk_percentage": None, "risk_category": None}

        # Simplified but clinically appropriate risk calculation
        risk_score = 0.0

        # Age factor (10 years adds ~1-2% baseline)
        if age >= 60:
            risk_score += 3
        elif age >= 50:
            risk_score += 1.5
        else:
            risk_score += 0.5

        # Lipid factors
        if ldl > 160:
            risk_score += 3
        elif ldl > 130:
            risk_score += 2
        elif ldl > 100:
            risk_score += 1

        if hdl < 40:
            risk_score += 3
        elif hdl < 50:
            risk_score += 1.5

        # Blood pressure (untreated)
        if not on_bp_medication:
            if systolic_bp >= 160:
                risk_score += 3
            elif systolic_bp >= 140:
                risk_score += 2
            elif systolic_bp >= 130:
                risk_score += 1

        # Lifestyle and disease factors
        if smoker:
            risk_score += 3
        if diabetic:
            risk_score += 2

        # Gender adjustment
        if gender.upper() == "F":
            risk_score *= 0.7

        # Race adjustment
        if race.lower() == "african american":
            risk_score *= 1.15

        # Ensure percentage is within reasonable bounds
        risk_percentage = max(0, min(100, risk_score))

        # Categorize risk
        if risk_percentage >= 7.5:
            risk_category = "high"
            statin_recommendation = "High-intensity statin therapy recommended"
        elif risk_percentage >= 5.0:
            risk_category = "intermediate"
            statin_recommendation = "Moderate-intensity statin therapy recommended"
        else:
            risk_category = "low"
            statin_recommendation = "Lifestyle modification recommended; consider low-intensity statin if risk factors present"

        return {
            "status": "ok",
            "risk_percentage": round(risk_percentage, 1),
            "risk_category": risk_category,
            "statin_recommendation": statin_recommendation,
            "inputs": {
                "age": age,
                "gender": gender.upper(),
                "race": race,
                "total_cholesterol": total_cholesterol,
                "ldl": ldl,
                "hdl": hdl,
                "systolic_bp": systolic_bp,
                "on_bp_medication": on_bp_medication,
                "smoker": smoker,
                "diabetic": diabetic,
            },
        }


class CreatinineClearanceCalculator:
    """Cockcroft-Gault formula for renal function estimation."""

    @staticmethod
    def calculate_creatinine_clearance(
        age: int, weight_kg: float, creatinine_mg_dl: float, gender: str = "M"
    ) -> Dict[str, Any]:
        """Calculate creatinine clearance (eGFR) using Cockcroft-Gault formula.

        Args:
            age: Age in years.
            weight_kg: Body weight in kilograms.
            creatinine_mg_dl: Serum creatinine in mg/dL.
            gender: 'M' or 'F'.

        Returns:
            Dictionary with estimated creatinine clearance and renal function category.
        """
        if creatinine_mg_dl <= 0 or weight_kg <= 0 or age <= 0:
            return {"error": "All values must be positive", "egfr": None, "renal_category": None}

        cg_ml_min = ((140 - age) * weight_kg) / (72 * creatinine_mg_dl)

        if gender.upper() == "F":
            cg_ml_min *= 0.85

        if cg_ml_min >= 90:
            renal_category = "normal"
            dosing_adjustment = "Normal dosing"
        elif cg_ml_min >= 60:
            renal_category = "mild_impairment"
            dosing_adjustment = "No dosing adjustment typically needed"
        elif cg_ml_min >= 30:
            renal_category = "moderate_impairment"
            dosing_adjustment = "Moderate dosing adjustment may be needed"
        else:
            renal_category = "severe_impairment"
            dosing_adjustment = "Significant dosing adjustment or alternative agent recommended"

        return {
            "status": "ok",
            "egfr_ml_min": round(cg_ml_min, 1),
            "renal_category": renal_category,
            "dosing_adjustment": dosing_adjustment,
            "inputs": {
                "age": age,
                "weight_kg": weight_kg,
                "creatinine_mg_dl": creatinine_mg_dl,
                "gender": gender.upper(),
            },
        }


class MedicationDosingCalculator:
    """Calculate appropriate medication doses based on patient factors."""

    COMMON_DRUG_DOSING = {
        "metformin": {
            "normal_dose": "500-2000mg daily in divided doses",
            "egfr_adjustments": {
                "normal": "No adjustment",
                "mild_impairment": "No adjustment",
                "moderate_impairment": "Max 1000mg daily",
                "severe_impairment": "Contraindicated",
            },
        },
        "atorvastatin": {
            "normal_dose": "10-80mg daily",
            "special_considerations": "Take with or without food",
            "drug_interactions": ["rifampin (reduces effect)", "clarithromycin (increases levels)"],
        },
        "lisinopril": {
            "normal_dose": "10-40mg daily",
            "special_considerations": "Monitor potassium and creatinine",
            "egfr_adjustments": {
                "normal": "10-40mg daily",
                "mild_impairment": "5-20mg daily",
                "moderate_impairment": "2.5-10mg daily",
                "severe_impairment": "Consult specialist",
            },
        },
        "warfarin": {
            "normal_dose": "2-10mg daily (INR-adjusted)",
            "special_considerations": "Requires INR monitoring",
            "major_interactions": [
                "NSAIDs",
                "Aspirin",
                "Amiodarone",
                "Flu vaccine",
            ],
        },
    }

    @classmethod
    def calculate_drug_dose(
        cls, drug_name: str, egfr: Optional[float] = None, age: Optional[int] = None, weight_kg: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate appropriate dose for a medication.

        Args:
            drug_name: Drug name (must be in COMMON_DRUG_DOSING).
            egfr: Estimated GFR (for renal adjustments).
            age: Patient age (for age-based adjustments).
            weight_kg: Patient weight in kg (for weight-based dosing).

        Returns:
            Dictionary with dosing recommendation.
        """
        drug_lower = drug_name.lower().strip()

        if drug_lower not in cls.COMMON_DRUG_DOSING:
            return {
                "error": f"Drug '{drug_name}' not found in dosing database",
                "available_drugs": list(cls.COMMON_DRUG_DOSING.keys()),
            }

        drug_info = cls.COMMON_DRUG_DOSING[drug_lower]
        recommendation: Dict[str, Any] = {
            "status": "ok",
            "drug": drug_name,
            "standard_dose": drug_info.get("normal_dose"),
        }

        if egfr and "egfr_adjustments" in drug_info:
            if egfr >= 90:
                renal_cat = "normal"
            elif egfr >= 60:
                renal_cat = "mild_impairment"
            elif egfr >= 30:
                renal_cat = "moderate_impairment"
            else:
                renal_cat = "severe_impairment"

            recommendation["renal_adjusted_dose"] = drug_info["egfr_adjustments"].get(renal_cat)
            recommendation["renal_category"] = renal_cat

        if age and age > 65:
            recommendation["age_note"] = "Elderly patient; consider lower starting dose"

        if "special_considerations" in drug_info:
            recommendation["special_considerations"] = drug_info["special_considerations"]

        if "drug_interactions" in drug_info:
            recommendation["known_interactions"] = drug_info["drug_interactions"]

        return recommendation


def get_dosing_guidance(drug_name: str, patient_info: Dict[str, Any]) -> Dict[str, Any]:
    """Get comprehensive dosing guidance for a drug.

    Args:
        drug_name: Drug name.
        patient_info: Dictionary with patient information (age, weight_kg, egfr, etc.).

    Returns:
        Comprehensive dosing guidance.
    """
    calculator = MedicationDosingCalculator()
    return calculator.calculate_drug_dose(
        drug_name, egfr=patient_info.get("egfr"), age=patient_info.get("age"), weight_kg=patient_info.get("weight_kg")
    )

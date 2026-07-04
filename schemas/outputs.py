from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GuidelineOutput:
    recommendations: List[str] = field(default_factory=list)
    evidence_sources: List[str] = field(default_factory=list)
    confidence: str = "low"


@dataclass
class MedicationSafetyOutput:
    interactions: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    safe_to_proceed: bool = True


@dataclass
class RiskOutput:
    score: float = 0.0
    classification: str = "Unknown"
    factors: List[str] = field(default_factory=list)


@dataclass
class PatientOutput:
    summary: str = ""
    lifestyle_advice: List[str] = field(default_factory=list)


@dataclass
class FinalReport:
    patient_data: dict = field(default_factory=dict)
    query: str = ""
    guidelines: Optional[GuidelineOutput] = None
    medication_safety: Optional[MedicationSafetyOutput] = None
    risk: Optional[RiskOutput] = None
    patient_communication: Optional[PatientOutput] = None
    error: Optional[str] = None

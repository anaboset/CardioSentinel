"""Configuration and constants for CardioSentinel MAS."""

import os
from enum import Enum
from typing import Final

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME: Final[str] = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Workflow Configuration
MAX_RETRIES: Final[int] = 3
RETRY_BACKOFF: Final[float] = 2.0
TIMEOUT_SECONDS: Final[int] = 60
MAX_LOOP_ITERATIONS: Final[int] = 10

# Risk Classification Thresholds (ASCVD 10-year risk %)
RISK_THRESHOLDS = {
    "low": 5,
    "moderate": 7.5,
    "high": 20,
    "very_high": 20,  # HITL triggered at ≥20% ASCVD risk
}

# Approved States for HITL
class ApprovalState(str, Enum):
    """Human-in-the-loop approval states."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MODIFICATION = "needs_modification"
    APPROVED_WITH_MODIFICATIONS = "approved_with_modifications"


class AgentNames(str, Enum):
    """Agent identifiers."""
    ORCHESTRATOR = "orchestrator"
    GUIDELINE = "guideline"
    RISK = "risk"
    MEDICATION = "medication"
    PATIENT = "patient"


# Checkpoints requiring human review
HITL_CHECKPOINTS = {
    AgentNames.MEDICATION.value: "Medication Safety (Critical - Safety Check)",
    AgentNames.RISK.value: "Risk Stratification (Risk Factors)",
    AgentNames.GUIDELINE.value: "Clinical Guidelines (Recommendations)",
}

# Logging Configuration
LOG_FORMAT = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# UI Configuration
UI_PAGE_ICON = "🫀"
UI_LAYOUT = "wide"
UI_THEME = "dark"  # Can be "light", "dark", or "auto"

# Cardiovascular Color Palette
COLORS = {
    "primary": "#E63946",  # Cardiovascular red
    "secondary": "#457B9D",  # Clinical blue
    "success": "#2A9D8F",  # Healthy green
    "warning": "#F4A261",  # Alert orange
    "danger": "#E63946",  # Critical red
    "info": "#264653",  # Dark slate
    "light": "#F1FAEE",  # Off-white
    "dark": "#1A1A1A",  # Near black
    "ecg_line": "#00D084",  # ECG green
}

# ECG Animation Configuration
ECG_CONFIG = {
    "wave_height": 20,
    "frequency": 2,
    "animation_duration": 2,
}

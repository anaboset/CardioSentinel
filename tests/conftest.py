import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from schemas.outputs import GuidelineOutput, RiskOutput


@pytest.fixture
def standard_patient():
    return {
        "age": 65,
        "bp": "150/95",
        "ldl": 160,
        "conditions": ["hypertension", "smoker"],
    }


@pytest.fixture
def healthy_patient():
    return {
        "age": 30,
        "bp": "115/75",
        "ldl": 95,
        "conditions": [],
    }


@pytest.fixture
def high_risk_patient():
    return {
        "age": 72,
        "bp": "170/105",
        "ldl": 210,
        "conditions": ["hypertension", "diabetes", "smoker"],
    }


@pytest.fixture
def mock_guidelines():
    return GuidelineOutput(
        recommendations=["Take ACE inhibitor daily.", "Quit smoking."],
        evidence_sources=["ACC/AHA 2023"],
        confidence="high",
    )


@pytest.fixture
def mock_risk():
    return RiskOutput(
        score=72,
        classification="Very High",
        factors=["Age 65", "Active smoker", "Stage 2 hypertension"],
    )


@pytest.fixture
def mock_claude_response():
    return '{"summary": "Your blood pressure is high.", "lifestyle_advice": ["Exercise daily.", "Quit smoking.", "Reduce salt."]}'

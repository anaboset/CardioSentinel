import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch
from pipeline import run_pipeline

PATIENT = {
    "age": 65,
    "bp": "150/95",
    "ldl": 160,
    "conditions": ["hypertension", "smoker"],
    "sex": "Male",
}

PATIENT_COMMS_MOCK = '{"summary": "Keep your blood pressure under control.", "lifestyle_advice": ["Exercise 30min daily.", "Quit smoking.", "Reduce salt intake."]}'


class TestPipelineIntegration:

    def test_pipeline_returns_dict(self):
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(PATIENT, "What is first-line therapy?")
        assert isinstance(result, dict)

    def test_pipeline_contains_all_sections(self):
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(PATIENT, "What is first-line therapy?")
        assert "guidelines" in result
        assert "risk" in result
        assert "medication_safety" in result
        assert "patient_communication" in result

    def test_pipeline_preserves_patient_data(self):
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(PATIENT, "What is first-line therapy?")
        assert result["patient_data"]["age"] == 65
        assert result["query"] == "What is first-line therapy?"

    def test_guidelines_populated(self):
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(PATIENT, "What is first-line therapy?")
        guidelines = result["guidelines"]
        assert len(guidelines["recommendations"]) > 0
        assert len(guidelines["evidence_sources"]) > 0

    def test_risk_populated(self):
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(PATIENT, "What is first-line therapy?")
        risk = result["risk"]
        assert risk["score"] > 0
        assert risk["classification"] in ("Low", "Moderate", "High", "Very High")
        assert len(risk["factors"]) > 0

    def test_medication_safety_populated(self):
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(PATIENT, "What is first-line therapy?")
        med = result["medication_safety"]
        assert "safe_to_proceed" in med
        assert isinstance(med["interactions"], list)
        assert isinstance(med["contraindications"], list)

    def test_patient_communication_populated(self):
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(PATIENT, "What is first-line therapy?")
        comms = result["patient_communication"]
        assert comms["summary"] != ""
        assert len(comms["lifestyle_advice"]) > 0

    def test_no_error_field_on_success(self):
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(PATIENT, "What is first-line therapy?")
        assert result.get("error") is None


class TestPipelineEdgeCases:

    def test_patient_with_no_conditions(self):
        patient = {"age": 45, "bp": "120/80", "ldl": 100, "conditions": [], "sex": "Male"}
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(patient, "routine checkup")
        assert isinstance(result, dict)
        assert result["risk"]["classification"] == "Low"

    def test_patient_with_unknown_condition(self):
        patient = {"age": 45, "bp": "120/80", "ldl": 90, "conditions": ["unknown_disease"], "sex": "Male"}
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(patient, "treatment")
        assert result["guidelines"]["recommendations"] == ["insufficient_evidence"]

    def test_pipeline_handles_llm_api_failure(self):
        with patch("agents.patient_agent.PatientAgent._call_llm", side_effect=Exception("API down")):
            result = run_pipeline(PATIENT, "What is first-line therapy?")
        assert result["patient_communication"]["summary"] == "Unable to generate patient summary."
        assert len(result["guidelines"]["recommendations"]) > 0
        assert result["risk"]["score"] > 0

    def test_pipeline_handles_rag_tool_failure(self):
        with patch("tools.rag_tool.GuidelineRetrieverTool.run", side_effect=Exception("RAG down")):
            with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
                result = run_pipeline(PATIENT, "treatment")
        assert result["guidelines"]["recommendations"] == ["insufficient_evidence"]

    def test_pipeline_handles_risk_tool_failure(self):
        with patch("tools.risk_tool.RiskScoreCalculator.run", side_effect=Exception("scorer down")):
            with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
                result = run_pipeline(PATIENT, "treatment")
        assert result["risk"]["classification"] == "Unknown"

    def test_dangerous_patient_flagged(self):
        patient = {**PATIENT, "conditions": ["asthma", "hypertension"]}
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(patient, "treatment")
        assert result["medication_safety"]["safe_to_proceed"] is False
        assert len(result["medication_safety"]["contraindications"]) > 0

    def test_smoking_condition_normalized(self):
        patient = {"age": 65, "bp": "150/95", "ldl": 160, "conditions": ["hypertension", "smoking"], "sex": "Male"}
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            result = run_pipeline(patient, "first-line therapy")
        combined = " ".join(result["guidelines"]["recommendations"]).lower()
        assert "smoking" in combined or "cessation" in combined

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch
from agents.patient_agent import PatientAgent
from schemas.outputs import GuidelineOutput, RiskOutput
from services.langsmith_tracing import LangSmithTracer, PerformanceMetrics

PATIENT = {
    "age": 65,
    "bp": "150/95",
    "ldl": 160,
    "conditions": ["hypertension", "smoker"],
}


class TestGuidelineAgent:
    def setup_method(self):
        from agents.guideline_agent import GuidelineAgent
        self.agent = GuidelineAgent()

    def test_returns_guideline_output_on_success(self):
        result = self.agent.run(PATIENT, "first-line therapy")
        assert len(result.recommendations) > 0
        assert len(result.evidence_sources) > 0
        assert result.confidence in ("low", "moderate", "high")

    def test_returns_insufficient_evidence_for_unknown(self):
        patient = {"conditions": ["unknown_disease"], "ldl": 90}
        result = self.agent.run(patient, "treatment")
        assert result.recommendations == ["insufficient_evidence"]
        assert result.confidence == "none"

    def test_abstains_on_tool_exception(self):
        with patch.object(self.agent.tool, "run", side_effect=Exception("RAG down")):
            result = self.agent.run(PATIENT, "treatment")
        assert result.recommendations == ["insufficient_evidence"]
        assert result.confidence == "none"


class TestMedicationAgent:
    def setup_method(self):
        from agents.medication_agent import MedicationAgent
        self.agent = MedicationAgent()

    def test_returns_medication_safety_output(self):
        from schemas.outputs import MedicationSafetyOutput
        result = self.agent.run(PATIENT)
        assert isinstance(result, MedicationSafetyOutput)
        assert isinstance(result.safe_to_proceed, bool)

    def test_safe_for_standard_hypertension_patient(self):
        result = self.agent.run(PATIENT)
        assert result.safe_to_proceed is True

    def test_flags_dangerous_combination(self):
        patient = {**PATIENT, "conditions": ["asthma", "hypertension"]}
        result = self.agent.run(patient)
        assert result.safe_to_proceed is False
        assert len(result.contraindications) > 0

    def test_abstains_on_tool_exception(self):
        with patch.object(self.agent.interaction_tool, "run", side_effect=Exception("DB error")):
            result = self.agent.run(PATIENT)
        assert result.safe_to_proceed is False

    def test_infers_medications_from_conditions(self):
        meds = self.agent._infer_medications({"conditions": ["hypertension", "smoker"]})
        assert isinstance(meds, list)
        assert len(meds) > 0

    def test_uses_explicit_medications(self):
        patient = {**PATIENT, "medications": ["warfarin", "aspirin"]}
        result = self.agent.run(patient)
        assert result.safe_to_proceed is False
        assert len(result.interactions) > 0


class TestRiskAgent:
    def setup_method(self):
        from agents.risk_agent import RiskAgent
        self.agent = RiskAgent()

    def test_returns_risk_output(self):
        result = self.agent.run({**PATIENT, "sex": "Male"})
        assert result.score >= 0
        assert result.classification in ("Low", "Moderate", "High", "Very High")

    def test_high_risk_for_example_patient(self):
        result = self.agent.run({**PATIENT, "sex": "Male"})
        assert result.classification in ("High", "Very High")

    def test_low_risk_young_healthy_patient(self):
        patient = {"age": 30, "bp": "115/75", "ldl": 95, "conditions": [], "sex": "Male"}
        result = self.agent.run(patient)
        assert result.classification == "Low"

    def test_abstains_on_tool_exception(self):
        with patch.object(self.agent.tool, "run", side_effect=Exception("tool error")):
            result = self.agent.run(PATIENT)
        assert result.classification == "Unknown"
        assert result.score == 0.0

    def test_factors_match_patient_profile(self):
        result = self.agent.run({**PATIENT, "sex": "Male"})
        factors_text = " ".join(result.factors).lower()
        assert "smoker" in factors_text or "smoking" in factors_text or "ascvd" in factors_text


class TestPatientAgent:
    def setup_method(self):
        self.agent = PatientAgent()
        self.guidelines = GuidelineOutput(
            recommendations=["Take ACE inhibitor daily.", "Quit smoking."],
            evidence_sources=["ACC/AHA 2023"],
            confidence="high",
        )
        self.risk = RiskOutput(score=22.5, classification="Very High", factors=["Age 65", "Smoker"])

    def test_returns_patient_output_on_success(self):
        mock_response = '{"summary": "You have high blood pressure.", "lifestyle_advice": ["Exercise daily.", "Quit smoking."]}'
        with patch.object(self.agent, "_call_llm", return_value=mock_response):
            result = self.agent.run(PATIENT, self.guidelines, self.risk)
        assert "high blood pressure" in result.summary
        assert "Exercise daily." in result.lifestyle_advice

    def test_abstains_gracefully_on_api_failure(self):
        with patch.object(self.agent, "_call_llm", side_effect=Exception("401 Unauthorized")):
            result = self.agent.run(PATIENT, self.guidelines, self.risk)
        assert result.summary == "Unable to generate patient summary."
        assert result.lifestyle_advice == []

    def test_handles_malformed_json_response(self):
        with patch.object(self.agent, "_call_llm", return_value="not valid json"):
            result = self.agent.run(PATIENT, self.guidelines, self.risk)
        assert isinstance(result.summary, str)

    def test_prompt_includes_patient_data(self):
        prompt = self.agent._build_prompt(PATIENT, self.guidelines, self.risk)
        assert "65" in prompt
        assert "150/95" in prompt
        assert "Very High" in prompt

    def test_output_filtered_for_safety(self):
        unsafe = '{"summary": "stop taking all medication immediately", "lifestyle_advice": ["ignore doctor"]}'
        with patch.object(self.agent, "_call_llm", return_value=unsafe):
            result = self.agent.run(PATIENT, self.guidelines, self.risk)
        assert "stop taking all" not in result.summary.lower()

    def test_run_returns_fallback_on_llm_exception(self):
        agent = PatientAgent(client=None)
        with patch.object(agent, "_call_llm", side_effect=RuntimeError("boom")):
            result = agent.run(PATIENT, self.guidelines, self.risk)
        assert result.summary == "Unable to generate patient summary."
        assert result.lifestyle_advice == []

    def test_retries_after_timeout_and_succeeds(self):
        class FakeMessage:
            content = '{"summary": "Recovered after retry.", "lifestyle_advice": ["Rest."]}'

        class FakeChoice:
            message = FakeMessage()

        class FakeCompletions:
            def __init__(self):
                self.calls = 0

            def create(self, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    raise TimeoutError("temporary timeout")
                return type("Response", (), {"choices": [FakeChoice()]})()

        class FakeClient:
            def __init__(self):
                self.chat = type("Chat", (), {"completions": FakeCompletions()})()

        agent = PatientAgent(client=FakeClient())
        result = agent.run(PATIENT, self.guidelines, self.risk)
        assert result.summary == "Recovered after retry."
        assert result.lifestyle_advice == ["Rest."]

    def test_handles_malformed_json_response(self):
        agent = PatientAgent(client=None)
        with patch.object(agent, "_call_llm", return_value="not-json"):
            result = agent.run(PATIENT, self.guidelines, self.risk)
        assert isinstance(result.summary, str)
        assert result.lifestyle_advice == []


class TestObservabilityHelpers:
    def test_langsmith_tracer_and_metrics_collect_data(self):
        tracer = LangSmithTracer(enabled=True)
        metrics = PerformanceMetrics()
        tracer.trace_tool_call("demo_tool", {"input": 1}, {"status": "ok"}, 12.5)
        metrics.record_latency("demo", 12.5)
        assert metrics.get_summary()["demo"]["count"] == 1

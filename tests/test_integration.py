import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch
from core.graph import run_workflow, build_cardiosentinel_graph
from core.edge_routing import create_edge_functions
from schemas.state import WorkflowState

PATIENT_COMMS = '{"summary": "Summary.", "lifestyle_advice": ["Tip 1."]}'


class TestGraphWorkflow:
    def test_workflow_completes(self):
        patient = {
            "age": 65, "bp": "150/95", "ldl": 160,
            "conditions": ["hypertension", "smoker"], "sex": "Male",
        }
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS):
            state = run_workflow(patient, "first-line therapy?")
        assert state.workflow_status == "completed"
        assert state.guidelines is not None
        assert state.risk is not None
        assert state.medication_safety is not None

    def test_audit_trail_populated(self):
        patient = {"age": 50, "bp": "130/85", "ldl": 120, "conditions": ["hypertension"], "sex": "Male"}
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS):
            state = run_workflow(patient, "treatment options")
        assert len(state.audit_trail) >= 4

    def test_validation_failure_marks_failed(self):
        state = run_workflow({}, "")
        assert state.workflow_status == "failed"
        assert state.error_message is not None

    def test_graph_builds_without_error(self):
        graph = build_cardiosentinel_graph()
        assert graph is not None


class TestEdgeRouting:
    def test_high_risk_flags_hitl_but_routes_to_medication(self):
        edges = create_edge_functions()
        state = WorkflowState(
            patient_data={}, query="test",
            risk=type("R", (), {"score": 25.0, "classification": "Very High"})(),
        )
        route = edges["route_after_risk"](state)
        assert route == "medication"
        assert state.human_review_needed is True

    def test_moderate_risk_routes_to_medication(self):
        edges = create_edge_functions()
        state = WorkflowState(
            patient_data={}, query="test",
            risk=type("R", (), {"score": 10.0, "classification": "Moderate"})(),
        )
        route = edges["route_after_risk"](state)
        assert route == "medication"

    def test_unsafe_medication_flags_hitl_but_routes_to_patient(self):
        edges = create_edge_functions()
        state = WorkflowState(
            patient_data={}, query="test",
            medication_safety=type("M", (), {"safe_to_proceed": False})(),
        )
        route = edges["route_after_medication"](state)
        assert route == "patient"
        assert state.human_review_needed is True

    def test_skip_review_when_no_decisions(self):
        edges = create_edge_functions()
        state = WorkflowState(patient_data={}, query="test", human_decisions=[])
        route = edges["route_after_review"](state)
        assert route == "skip_review"

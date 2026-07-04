import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

PATIENT_COMMS_MOCK = '{"summary": "Test summary.", "lifestyle_advice": ["Exercise."]}'


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data

    def test_health_lists_services(self, client):
        response = client.get("/api/v1/health")
        assert "services" in response.json()


class TestAnalyzeEndpoint:
    def test_analyze_success(self, client):
        payload = {
            "patient": {
                "age": 65, "bp": "150/95", "ldl": 160,
                "conditions": ["hypertension"], "sex": "Male",
            },
            "query": "What is first-line therapy?",
        }
        with patch("agents.patient_agent.PatientAgent._call_llm", return_value=PATIENT_COMMS_MOCK):
            response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["risk"] is not None
        assert data["data"]["guidelines"] is not None

    def test_analyze_invalid_bp(self, client):
        payload = {
            "patient": {"age": 65, "bp": "invalid", "ldl": 160, "conditions": []},
            "query": "test query here",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    def test_analyze_missing_query(self, client):
        payload = {
            "patient": {"age": 65, "bp": "150/95", "ldl": 160, "conditions": []},
            "query": "ab",
        }
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422


class TestGuidelinesSearch:
    def test_search_returns_results(self, client):
        response = client.get("/api/v1/guidelines/search?q=hypertension&conditions=hypertension")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0

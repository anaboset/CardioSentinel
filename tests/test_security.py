import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch
from security.validation import validate_patient_input, validate_query, ValidationError
from security.content_filter import filter_output, filter_patient_output


class TestInputValidation:
    def test_valid_patient(self):
        patient, warnings = validate_patient_input({
            "age": 65, "bp": "150/95", "ldl": 160,
            "conditions": ["hypertension", "smoking"],
        })
        assert patient["age"] == 65
        assert "smoker" in patient["conditions"]

    def test_missing_age_raises(self):
        with pytest.raises(ValidationError):
            validate_patient_input({"bp": "120/80", "ldl": 100})

    def test_invalid_bp_format(self):
        with pytest.raises(ValidationError):
            validate_patient_input({"age": 50, "bp": "high", "ldl": 100})

    def test_age_out_of_range(self):
        with pytest.raises(ValidationError):
            validate_patient_input({"age": 10, "bp": "120/80", "ldl": 100})

    def test_query_validation(self):
        assert validate_query("What is first-line therapy?") == "What is first-line therapy?"

    def test_empty_query_raises(self):
        with pytest.raises(ValidationError):
            validate_query("")

    def test_injection_sanitized(self):
        patient, _ = validate_patient_input({
            "age": 50, "bp": "120/80", "ldl": 100,
            "conditions": [], "medications": ["<script>alert(1)</script>"],
        })
        assert "<script>" not in patient["medications"][0]


class TestContentFilter:
    def test_filters_unsafe_content(self):
        result = filter_output("You should stop taking all medication immediately.")
        assert "stop taking all" not in result.lower()

    def test_adds_disclaimer(self):
        result = filter_output("Your blood pressure is elevated.")
        assert "professional medical advice" in result.lower()

    def test_patient_output_filter(self):
        result = filter_patient_output("Test summary.", ["Exercise daily."])
        assert "disclaimer" in result["summary"].lower() or "professional" in result["summary"].lower()

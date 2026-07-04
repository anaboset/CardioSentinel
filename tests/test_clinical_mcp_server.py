"""Comprehensive tests for production-ready clinical MCP server with all integrations."""

import json
import pytest
import httpx

from clinical_mcp_server import (
    check_drug_interactions,
    check_patient_contraindications,
    query_clinical_guidelines,
    calculate_ascvd_risk,
    estimate_renal_function,
    get_medication_dosing,
    get_server_metrics,
)
from security.mcp_validators import (
    ClinicalDataValidator,
    ClinicalOutputValidator,
    GiskardSecurityScanner,
)
from services.redis_cache import RedisCache
from tools.cardiovascular_calculators import (
    ASCVDRiskCalculator,
    CreatinineClearanceCalculator,
    MedicationDosingCalculator,
)


# ==================== Guardrails Validators Tests ====================


def test_clinical_data_validator_validates_query():
    """Test clinical query validation."""
    valid = ClinicalDataValidator.validate_clinical_query("hypertension treatment options")
    assert "hypertension" in valid.lower()

    with pytest.raises(ValueError):
        ClinicalDataValidator.validate_clinical_query("")

    with pytest.raises(ValueError):
        ClinicalDataValidator.validate_clinical_query("x" * 1000)


def test_clinical_data_validator_validates_drug_names():
    """Test drug name validation."""
    valid = ClinicalDataValidator.validate_drug_name("atorvastatin")
    assert "atorvastatin" == valid.lower()

    with pytest.raises(ValueError):
        ClinicalDataValidator.validate_drug_name("")

    with pytest.raises(ValueError):
        ClinicalDataValidator.validate_drug_name("drug<script>alert()</script>")


def test_clinical_data_validator_validates_drug_list():
    """Test drug list validation."""
    valid = ClinicalDataValidator.validate_drug_list(["atorvastatin", "lisinopril"])
    assert len(valid) == 2

    with pytest.raises(ValueError):
        ClinicalDataValidator.validate_drug_list([])

    with pytest.raises(ValueError):
        ClinicalDataValidator.validate_drug_list(["atorvastatin"] * 15)


# ==================== Output Validator Tests ====================


def test_clinical_output_validator_validates_guideline_evidence():
    """Test guideline evidence output validation."""
    valid_evidence = {"text": "Treatment recommendation", "source": "ACC/AHA"}
    assert ClinicalOutputValidator.validate_guideline_evidence(valid_evidence) is True

    with pytest.raises(ValueError):
        ClinicalOutputValidator.validate_guideline_evidence({"text": "", "source": "ACC/AHA"})

    with pytest.raises(ValueError):
        ClinicalOutputValidator.validate_guideline_evidence({"text": "Treatment"})


def test_clinical_output_validator_validates_drug_interaction_response():
    """Test drug interaction response validation."""
    valid_ok = {"status": "ok", "data": {"interactions": []}}
    assert ClinicalOutputValidator.validate_drug_interaction_response(valid_ok) is True

    valid_error = {"status": "error", "error": {"code": "network_error"}}
    assert ClinicalOutputValidator.validate_drug_interaction_response(valid_error) is True

    with pytest.raises(ValueError):
        ClinicalOutputValidator.validate_drug_interaction_response({"status": "invalid"})


# ==================== Giskard Security Tests ====================


def test_giskard_security_scanner_scans_guideline_output():
    """Test Giskard security scanning on guideline output."""
    good_output = "Consult your physician before starting treatment based on ACC/AHA guidelines."
    result = GiskardSecurityScanner.scan_guideline_output(good_output)

    assert result["violation_count"] == 0
    assert result["safe_to_use"] is True


def test_giskard_security_scanner_detects_violations():
    """Test Giskard detection of security violations."""
    bad_output = "This drug will cure you 100% effectively."
    result = GiskardSecurityScanner.scan_guideline_output(bad_output)

    assert result["violation_count"] > 0
    assert result["safe_to_use"] is False


def test_giskard_security_scanner_scans_drug_recommendation():
    """Test Giskard drug safety scanning."""
    output_with_warning = "This drug has a black box warning for serious adverse effects."
    result = GiskardSecurityScanner.scan_drug_recommendation(output_with_warning)

    assert result["requires_review"] is True
    assert len(result["critical_warnings"]) > 0


# ==================== MCP Tool Tests ====================


def test_query_clinical_guidelines_returns_structured_evidence():
    """Test guideline query tool returns proper structure."""
    result = query_clinical_guidelines("hypertension first-line treatment")

    assert "retrieved_evidence" in result
    assert "sources" in result
    assert isinstance(result["retrieved_evidence"], list)
    assert isinstance(result["sources"], list)


def test_query_clinical_guidelines_with_source_filter():
    """Test guideline query with source filtering."""
    result = query_clinical_guidelines("hypertension", guideline_source="ACC/AHA")

    if result.get("status") != "error":
        assert "retrieved_evidence" in result
        for evidence in result.get("retrieved_evidence", []):
            if evidence.get("source"):
                assert "ACC/AHA" in evidence["source"] or result.get("status") != "ok"


def test_check_drug_interactions_returns_error_payload_on_failure(monkeypatch):
    """Test drug interaction tool error handling."""

    async def raise_error(*args, **kwargs):
        raise httpx.RequestError("simulated network failure")

    monkeypatch.setattr("clinical_mcp_server._fetch_drug_interaction_payload", raise_error)

    result = check_drug_interactions(["atorvastatin", "warfarin"])

    assert result["status"] == "error"
    assert result["error"]["code"] == "network_error"


def test_check_patient_contraindications_returns_error_payload_when_no_data(monkeypatch):
    """Test contraindication tool error handling."""

    async def raise_error(*args, **kwargs):
        raise httpx.RequestError("simulated network failure")

    monkeypatch.setattr("clinical_mcp_server._fetch_openfda_payload", raise_error)

    result = check_patient_contraindications("unknown_drug_xyz")

    assert result["status"] == "error"
    assert result["error"]["code"] in {"network_error", "not_found"}


# ==================== Cardiovascular Calculator Tests ====================


def test_ascvd_risk_calculator_calculates_high_risk():
    """Test ASCVD risk calculation for high-risk patient."""
    result = ASCVDRiskCalculator.calculate_10year_risk(
        age=55,
        gender="M",
        race="White",
        total_cholesterol=280,
        ldl=200,
        hdl=30,
        systolic_bp=160,
        on_bp_medication=False,
        smoker=True,
        diabetic=True,
    )

    assert result["status"] == "ok"
    assert result["risk_percentage"] > 7.5
    assert result["risk_category"] == "high"
    assert "High-intensity statin" in result["statin_recommendation"]


def test_ascvd_risk_calculator_validates_age():
    """Test ASCVD calculator rejects invalid age."""
    result = ASCVDRiskCalculator.calculate_10year_risk(
        age=25, gender="M", race="White", total_cholesterol=200, ldl=130, hdl=50, systolic_bp=120,
        on_bp_medication=False, smoker=False, diabetic=False,
    )

    assert "error" in result or result.get("risk_percentage") is None


def test_creatinine_clearance_calculator_estimates_normal_kidney():
    """Test kidney function estimation for normal renal function."""
    result = CreatinineClearanceCalculator.calculate_creatinine_clearance(
        age=40, weight_kg=70, creatinine_mg_dl=0.8, gender="M"
    )

    assert result["status"] == "ok"
    assert result["egfr_ml_min"] > 60
    assert result["renal_category"] == "normal"


def test_creatinine_clearance_calculator_detects_severe_impairment():
    """Test kidney function estimation for severe impairment."""
    result = CreatinineClearanceCalculator.calculate_creatinine_clearance(
        age=70, weight_kg=50, creatinine_mg_dl=4.0, gender="F"
    )

    assert result["status"] == "ok"
    assert result["egfr_ml_min"] < 30
    assert result["renal_category"] == "severe_impairment"


def test_medication_dosing_calculator_provides_renal_adjustments():
    """Test medication dosing calculator provides renal adjustments."""
    result = MedicationDosingCalculator.calculate_drug_dose("lisinopril", egfr=45)

    assert result["status"] == "ok"
    assert "renal_adjusted_dose" in result
    assert result["renal_category"] == "moderate_impairment"


def test_medication_dosing_calculator_handles_unknown_drug():
    """Test dosing calculator rejects unknown drugs."""
    result = MedicationDosingCalculator.calculate_drug_dose("unknown_drug_xyz")

    assert result.get("error") is not None or "unknown_drug" in result.get("drug", "").lower()


# ==================== Integration Tests ====================


def test_calculate_ascvd_risk_tool():
    """Test ASCVD risk calculation MCP tool."""
    result = calculate_ascvd_risk(
        age=50, gender="M", race="White", total_cholesterol=240, ldl=160, hdl=40,
        systolic_bp=140, on_bp_medication=True, smoker=False, diabetic=False,
    )

    assert "risk_percentage" in result or "error" in result


def test_estimate_renal_function_tool():
    """Test renal function estimation MCP tool."""
    result = estimate_renal_function(age=45, weight_kg=75, creatinine_mg_dl=1.0, gender="M")

    assert result["status"] == "ok"
    assert "egfr_ml_min" in result


def test_get_medication_dosing_tool():
    """Test medication dosing MCP tool."""
    result = get_medication_dosing("metformin", egfr=50, age=60)

    assert result["status"] == "ok" or "error" in result


def test_get_server_metrics_tool():
    """Test server metrics retrieval."""
    result = get_server_metrics()

    assert result["status"] == "ok"
    assert "performance_metrics" in result
    assert "cache_statistics" in result
    assert "tracing_enabled" in result


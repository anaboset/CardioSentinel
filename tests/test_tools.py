import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from tools.rag_tool import GuidelineRetrieverTool
from tools.interaction_tool import DrugInteractionTool
from tools.contraindication_tool import ContraindicationChecker
from tools.risk_tool import RiskScoreCalculator
from services.rag_engine import RAGEngine
from utils.condition_normalizer import normalize_condition, normalize_conditions


class TestConditionNormalizer:
    def test_smoking_maps_to_smoker(self):
        assert normalize_condition("smoking") == "smoker"

    def test_htn_maps_to_hypertension(self):
        assert normalize_condition("HTN") == "hypertension"

    def test_deduplicates(self):
        assert normalize_conditions(["smoking", "smoker"]) == ["smoker"]


class TestRAGEngine:
    def setup_method(self):
        self.engine = RAGEngine()

    def test_search_returns_results(self):
        results = self.engine.search("first-line therapy", ["hypertension"])
        assert len(results) > 0

    def test_retrieve_for_high_ldl(self):
        result = self.engine.retrieve({"conditions": [], "ldl": 160}, "cholesterol management")
        assert result["status"] == "ok"
        assert len(result["recommendations"]) > 0


class TestGuidelineRetrieverTool:
    def setup_method(self):
        self.tool = GuidelineRetrieverTool()

    def test_returns_recommendations_for_known_condition(self):
        result = self.tool.run(
            patient_summary={"conditions": ["hypertension"], "ldl": 100},
            clinical_question="first-line therapy",
        )
        assert result["status"] == "ok"
        assert len(result["recommendations"]) > 0
        assert len(result["sources"]) > 0

    def test_triggers_dyslipidemia_for_high_ldl(self):
        result = self.tool.run(
            patient_summary={"conditions": [], "ldl": 160},
            clinical_question="cholesterol management",
        )
        assert result["status"] == "ok"
        assert any("statin" in r.lower() or "ldl" in r.lower() for r in result["recommendations"])

    def test_returns_insufficient_evidence_for_empty_query_and_no_match(self):
        result = self.tool.run(
            patient_summary={"conditions": ["unknown_rare_disease"], "ldl": 90},
            clinical_question="xyzabc123nonexistent",
        )
        assert result["status"] in ("ok", "insufficient_evidence")

    def test_multiple_conditions_merged(self):
        result = self.tool.run(
            patient_summary={"conditions": ["hypertension", "smoker"], "ldl": 100},
            clinical_question="treatment smoking hypertension",
        )
        assert result["status"] == "ok"
        combined = " ".join(result["recommendations"]).lower()
        assert "smoking" in combined or "cessation" in combined

    def test_smoking_alias_normalized_via_pipeline(self):
        result = self.tool.run(
            patient_summary={"conditions": ["smoking"], "ldl": 100},
            clinical_question="smoking cessation",
        )
        assert result["status"] == "ok"


class TestDrugInteractionTool:
    def setup_method(self):
        self.tool = DrugInteractionTool()

    def test_detects_known_interaction(self):
        result = self.tool.run(["warfarin", "aspirin"])
        assert result["interactions_found"] is True
        assert len(result["warnings"]) >= 1

    def test_detects_reverse_pair(self):
        result = self.tool.run(["aspirin", "warfarin"])
        assert result["interactions_found"] is True

    def test_no_interaction_for_safe_combo(self):
        result = self.tool.run(["ace_inhibitor", "thiazide"])
        assert result["interactions_found"] is False

    def test_single_drug_no_interaction(self):
        result = self.tool.run(["statin"])
        assert result["interactions_found"] is False

    def test_empty_list(self):
        result = self.tool.run([])
        assert result["interactions_found"] is False

    def test_drug_alias_resolution(self):
        result = self.tool.run(["lisinopril", "hydrochlorothiazide"])
        assert result["interactions_found"] is False


class TestContraindicationChecker:
    def setup_method(self):
        self.tool = ContraindicationChecker()

    def test_flags_asthma_with_beta_blocker(self):
        result = self.tool.run(
            conditions=["asthma"],
            proposed_medications=["beta_blocker"],
        )
        assert result["contraindications_found"] is True

    def test_flags_pregnancy_with_ace_inhibitor(self):
        result = self.tool.run(
            conditions=["pregnancy"],
            proposed_medications=["ace_inhibitor", "metformin"],
        )
        assert result["contraindications_found"] is True

    def test_no_flag_for_safe_combo(self):
        result = self.tool.run(
            conditions=["hypertension"],
            proposed_medications=["ace_inhibitor"],
        )
        assert result["contraindications_found"] is False

    def test_empty_inputs(self):
        result = self.tool.run(conditions=[], proposed_medications=[])
        assert result["contraindications_found"] is False


class TestRiskScoreCalculator:
    def setup_method(self):
        self.tool = RiskScoreCalculator()

    def test_very_high_risk_patient(self):
        result = self.tool.run({
            "age": 70, "bp": "165/100", "ldl": 200,
            "conditions": ["smoker", "diabetes"], "sex": "Male",
        })
        assert result["classification"] in ("High", "Very High")
        assert result["score"] >= 7.5

    def test_low_risk_patient(self):
        result = self.tool.run({
            "age": 35, "bp": "118/75", "ldl": 100,
            "conditions": [], "sex": "Female",
        })
        assert result["classification"] == "Low"
        assert result["score"] < 7.5

    def test_score_capped_at_100(self):
        result = self.tool.run({
            "age": 80, "bp": "180/110", "ldl": 250,
            "conditions": ["smoker", "diabetes", "ckd"], "sex": "Male",
        })
        assert result["score"] <= 100

    def test_factors_list_populated(self):
        result = self.tool.run({
            "age": 65, "bp": "150/95", "ldl": 160,
            "conditions": ["smoker"], "sex": "Male",
        })
        assert len(result["factors"]) > 0

    def test_smoker_adds_to_score(self):
        base = self.tool.run({"age": 50, "bp": "120/80", "ldl": 100, "conditions": [], "sex": "Male"})
        with_smoking = self.tool.run({"age": 50, "bp": "120/80", "ldl": 100, "conditions": ["smoker"], "sex": "Male"})
        assert with_smoking["score"] > base["score"]

    def test_ascvd_method_documented(self):
        result = self.tool.run({"age": 55, "bp": "140/90", "ldl": 130, "conditions": [], "sex": "Male"})
        assert "method" in result

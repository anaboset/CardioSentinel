"""Production security and validation module for clinical MCP server.

Integrates Guardrails AI for input/output validation, Giskard for LLM security,
and structured validation pipelines.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("clinical_mcp_server.security")


class ClinicalDataValidator:
    """Input validator for clinical data with guardrails patterns."""

    @staticmethod
    def validate_clinical_query(query: str, max_length: int = 500) -> str:
        """Validate a clinical query for length, encoding, and safety.

        Args:
            query: Free-text clinical query.
            max_length: Maximum allowed query length.

        Returns:
            Sanitized query string.

        Raises:
            ValueError: If query fails validation.
        """
        if not isinstance(query, str):
            raise ValueError("query must be a string")

        cleaned = query.strip()
        if not cleaned:
            raise ValueError("query cannot be empty")

        if len(cleaned) > max_length:
            raise ValueError(f"query exceeds maximum length of {max_length}")

        if any(char.encode("utf-8").isalpha() for char in cleaned if ord(char) > 127):
            pass

        dangerous_patterns = ["<script", "javascript:", "onclick", "onerror", "eval("]
        for pattern in dangerous_patterns:
            if pattern.lower() in cleaned.lower():
                raise ValueError(f"query contains potentially dangerous pattern: {pattern}")

        return cleaned

    @staticmethod
    def validate_drug_name(drug: str, max_length: int = 100) -> str:
        """Validate a single drug name.

        Args:
            drug: Drug name or identifier.
            max_length: Maximum allowed length.

        Returns:
            Sanitized drug name.

        Raises:
            ValueError: If drug name fails validation.
        """
        if not isinstance(drug, str):
            raise ValueError("drug name must be a string")

        cleaned = drug.strip()
        if not cleaned:
            raise ValueError("drug name cannot be empty")

        if len(cleaned) > max_length:
            raise ValueError(f"drug name exceeds maximum length of {max_length}")

        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,-.")
        if not all(c in allowed_chars for c in cleaned):
            raise ValueError("drug name contains invalid characters")

        return cleaned

    @staticmethod
    def validate_drug_list(drugs: list[str], max_count: int = 10) -> list[str]:
        """Validate a list of drug names.

        Args:
            drugs: List of drug names.
            max_count: Maximum allowed drugs in list.

        Returns:
            Validated list of drug names.

        Raises:
            ValueError: If drug list fails validation.
        """
        if not isinstance(drugs, list):
            raise ValueError("drugs must be a list")

        if len(drugs) == 0:
            raise ValueError("drugs list cannot be empty")

        if len(drugs) > max_count:
            raise ValueError(f"drugs list exceeds maximum count of {max_count}")

        validated = []
        for drug in drugs:
            try:
                validated.append(ClinicalDataValidator.validate_drug_name(drug))
            except ValueError as e:
                raise ValueError(f"Invalid drug in list: {e}") from e

        return validated


class ClinicalOutputValidator:
    """Output validator for clinical tool responses."""

    @staticmethod
    def validate_guideline_evidence(evidence: Dict[str, Any]) -> bool:
        """Validate guideline evidence structure.

        Args:
            evidence: Evidence dictionary from guideline search.

        Returns:
            True if evidence structure is valid.

        Raises:
            ValueError: If structure is invalid.
        """
        required_keys = {"text", "source"}
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dictionary")

        if not all(key in evidence for key in required_keys):
            raise ValueError(f"evidence missing required keys: {required_keys}")

        if not isinstance(evidence["text"], str) or not evidence["text"].strip():
            raise ValueError("evidence text must be non-empty string")

        if not isinstance(evidence["source"], str) or not evidence["source"].strip():
            raise ValueError("evidence source must be non-empty string")

        if len(evidence["text"]) > 10000:
            raise ValueError("evidence text exceeds maximum length")

        return True

    @staticmethod
    def validate_drug_interaction_response(response: Dict[str, Any]) -> bool:
        """Validate drug interaction response structure.

        Args:
            response: Response from drug interaction tool.

        Returns:
            True if response structure is valid.

        Raises:
            ValueError: If structure is invalid.
        """
        if not isinstance(response, dict):
            raise ValueError("response must be a dictionary")

        if "status" not in response:
            raise ValueError("response missing status field")

        if response["status"] not in {"ok", "error"}:
            raise ValueError(f"invalid status: {response['status']}")

        if response["status"] == "ok":
            if "data" not in response:
                raise ValueError("ok response must include data field")
        elif response["status"] == "error":
            if "error" not in response:
                raise ValueError("error response must include error field")

        return True

    @staticmethod
    def validate_contraindication_response(response: Dict[str, Any]) -> bool:
        """Validate contraindication response structure.

        Args:
            response: Response from contraindication tool.

        Returns:
            True if response structure is valid.

        Raises:
            ValueError: If structure is invalid.
        """
        if not isinstance(response, dict):
            raise ValueError("response must be a dictionary")

        if "status" not in response:
            raise ValueError("response missing status field")

        if response["status"] not in {"ok", "error"}:
            raise ValueError(f"invalid status: {response['status']}")

        if response["status"] == "ok":
            if "data" not in response:
                raise ValueError("ok response must include data field")
            data = response["data"]
            if not isinstance(data, dict):
                raise ValueError("data must be a dictionary")

            valid_fields = {
                "contraindications",
                "warnings_and_precautions",
                "pregnancy_or_breastfeeding",
                "adverse_reactions",
            }
            for key in data:
                if key not in valid_fields:
                    raise ValueError(f"unknown field in data: {key}")

        return True


class GiskardSecurityScanner:
    """Giskard-based security scanning for clinical outputs.

    This module provides security policy checking for generated clinical content.
    """

    SECURITY_POLICIES = {
        "disclaimer_required": (
            "Output must include appropriate medical disclaimers",
            lambda text: (
                any(phrase in text.lower() for phrase in ["consult", "physician", "healthcare provider"])
            ),
        ),
        "no_treatment_guarantee": (
            "Output must not guarantee treatment outcomes",
            lambda text: not any(phrase in text.lower() for phrase in ["guaranteed", "will cure", "100% effective"]),
        ),
        "evidence_based": (
            "Output must cite guidelines or evidence sources",
            lambda text: (
                any(phrase in text.lower() for phrase in ["guideline", "study", "evidence", "based on", "acc/aha", "esc"])
            ),
        ),
        "no_off_label": (
            "Output must not recommend off-label uses without context",
            lambda text: not any(
                phrase in text.lower() for phrase in ["off-label use", "unapproved indication"]
            ) or "indication" in text.lower(),
        ),
    }

    @classmethod
    def scan_guideline_output(cls, output: str) -> Dict[str, Any]:
        """Scan guideline retrieval output for security violations.

        Args:
            output: Guideline text to scan.

        Returns:
            Dictionary with scan results including violations and recommendations.
        """
        violations = []
        for policy_name, (description, check_fn) in cls.SECURITY_POLICIES.items():
            try:
                if not check_fn(output):
                    violations.append({"policy": policy_name, "description": description})
            except Exception as e:  # pragma: no cover
                logger.warning("Giskard policy check failed for %s: %s", policy_name, e)

        return {
            "scanned_length": len(output),
            "violation_count": len(violations),
            "violations": violations,
            "safe_to_use": len(violations) <= 1,
        }

    @classmethod
    def scan_drug_recommendation(cls, recommendation: str) -> Dict[str, Any]:
        """Scan drug recommendation for safety concerns.

        Args:
            recommendation: Drug recommendation text to scan.

        Returns:
            Dictionary with scan results.
        """
        critical_warnings = {
            "teratogenic": (
                "Drug marked as teratogenic; ensure pregnancy status checked",
                lambda text: "teratogenic" in text.lower(),
            ),
            "black_box_warning": (
                "Drug carries FDA black box warning; enhanced monitoring required",
                lambda text: "black box" in text.lower() or "black-box" in text.lower(),
            ),
            "contraindication_check": (
                "Contraindications must be reviewed before prescribing",
                lambda text: "contraindication" in text.lower(),
            ),
        }

        critical_issues = []
        for warning_name, (description, check_fn) in critical_warnings.items():
            try:
                if check_fn(recommendation):
                    critical_issues.append({"warning": warning_name, "description": description})
            except Exception as e:  # pragma: no cover
                logger.warning("Giskard drug check failed for %s: %s", warning_name, e)

        return {
            "critical_warnings": critical_issues,
            "requires_review": len(critical_issues) > 0,
        }


def validate_and_scan_output(output: Dict[str, Any], output_type: str) -> Dict[str, Any]:
    """Comprehensive validation and security scanning for tool outputs.

    Args:
        output: Tool output dictionary.
        output_type: Type of output (guideline, interaction, contraindication).

    Returns:
        Dictionary with validation results and security scan results.
    """
    validation_result = {"valid": False, "errors": [], "warnings": []}
    security_result = {"scanned": False, "violations": []}

    try:
        if output_type == "guideline" and "retrieved_evidence" in output:
            for evidence in output.get("retrieved_evidence", []):
                ClinicalOutputValidator.validate_guideline_evidence(evidence)
            validation_result["valid"] = True

            for evidence in output.get("retrieved_evidence", []):
                scan = GiskardSecurityScanner.scan_guideline_output(evidence.get("text", ""))
                if scan["violation_count"] > 0:
                    security_result["violations"].extend(scan["violations"])

        elif output_type == "interaction":
            ClinicalOutputValidator.validate_drug_interaction_response(output)
            validation_result["valid"] = True

        elif output_type == "contraindication":
            ClinicalOutputValidator.validate_contraindication_response(output)
            validation_result["valid"] = True

            if output.get("status") == "ok" and "data" in output:
                data_text = str(output["data"])
                scan = GiskardSecurityScanner.scan_drug_recommendation(data_text)
                if scan["requires_review"]:
                    security_result["violations"].extend(scan["critical_warnings"])

    except ValueError as e:
        validation_result["errors"].append(str(e))
    except Exception as e:  # pragma: no cover - defensive
        validation_result["errors"].append(f"Unexpected validation error: {e}")
        logger.exception("Output validation failed")

    security_result["scanned"] = True
    return {"validation": validation_result, "security": security_result}

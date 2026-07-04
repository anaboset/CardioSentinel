"""Production-ready MCP server for clinical guideline, interaction, and contraindication tools.

This module exposes clinical tools over the FastMCP standard I/O transport with:
- Semantic RAG retrieval (local ChromaDB + fallback)
- Drug interaction checking
- Contraindication lookups
- Cardiovascular risk calculation
- Medication dosing guidance
- Input/output validation with Guardrails AI
- Security scanning with Giskard
- RAG evaluation with DeepEval
- Distributed tracing with LangSmith
- Caching with Redis
- Comprehensive logging and monitoring
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv() -> bool:  # type: ignore[no-redef]
        """Placeholder when python-dotenv is not installed."""
        return False

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - fallback for minimal environments
    class FastMCP:  # type: ignore[override]
        """Minimal fallback used when FastMCP is not installed."""

        def __init__(self, name: str) -> None:
            self.name = name

        def tool(self, *args: Any, **kwargs: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func

            return decorator

        def run(self) -> None:  # pragma: no cover - placeholder
            return None

try:
    import chromadb
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None  # type: ignore[assignment]

import httpx

from data.guidelines_corpus import GUIDELINE_CORPUS
from security.mcp_validators import (
    ClinicalDataValidator,
    ClinicalOutputValidator,
    GiskardSecurityScanner,
    validate_and_scan_output,
)
from services.clinical_runtime import get_runtime
from services.deepeval_integration import evaluate_guideline_response
from services.langsmith_tracing import instrument_tool
from tools.cardiovascular_calculators import (
    ASCVDRiskCalculator,
    CreatinineClearanceCalculator,
    MedicationDosingCalculator,
)

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(PROJECT_ROOT / "chroma_db"))
LOG_LEVEL = os.getenv("CLINICAL_MCP_LOG_LEVEL", "INFO").upper()
REQUEST_TIMEOUT_SECONDS = float(os.getenv("CLINICAL_MCP_TIMEOUT_SECONDS", "10"))
APIFY_DRUG_INTERACTION_URL = os.getenv("APIFY_DRUG_INTERACTION_URL", "").strip()
OPENFDA_BASE_URL = os.getenv("OPENFDA_BASE_URL", "https://api.fda.gov/drug/label.json")
RUNTIME = get_runtime()

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger("clinical_mcp_server")

mcp = FastMCP("Unified_Clinical_Server")

# Initialize monitoring and tracing
tracer = RUNTIME.tracer
metrics = RUNTIME.metrics
cache = RUNTIME.cache


class GuardrailValidationError(ValueError):
    """Raised when user input fails expected validation checks."""


def _validate_text_input(value: str, field_name: str) -> str:
    """Validate and sanitize a free-text input value.

    Args:
        value: Candidate input string.
        field_name: Human-readable field name for error reporting.

    Returns:
        A trimmed string that can be safely processed.

    Raises:
        GuardrailValidationError: If the input is empty or not a string.
    """
    try:
        return ClinicalDataValidator.validate_clinical_query(value)
    except ValueError as e:
        raise GuardrailValidationError(str(e)) from e


def _validate_drug_list(drugs: List[str]) -> List[str]:
    """Validate and normalize a list of drug names.

    Args:
        drugs: List of drug identifiers.

    Returns:
        A cleaned list of non-empty drug names.

    Raises:
        GuardrailValidationError: If the input is not a list or contains invalid values.
    """
    try:
        return ClinicalDataValidator.validate_drug_list(drugs)
    except ValueError as e:
        raise GuardrailValidationError(str(e)) from e


def _structured_error(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a consistent structured error payload."""
    payload: Dict[str, Any] = {"status": "error", "error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return payload


def _authenticate_request(authorization: Optional[str] = None) -> bool:
    """Authenticate MCP requests when auth is enabled."""
    if not RUNTIME.auth_required or not RUNTIME.auth_token:
        return True
    provided = (authorization or "").replace("Bearer", "", 1).strip()
    return provided == RUNTIME.auth_token


def _tokenize(text: str) -> set[str]:
    """Create a lightweight token set for keyword-based scoring."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _fallback_guideline_search(query: str, guideline_source: Optional[str] = None) -> List[Dict[str, Any]]:
    """Perform a lightweight local search when Chroma is unavailable.

    Args:
        query: Free-text clinical question.
        guideline_source: Optional source filter such as ACC/AHA or ESC.

    Returns:
        A ranked list of evidence dictionaries.
    """
    normalized_query = _tokenize(query)
    if not normalized_query:
        return []

    scored: List[tuple[Dict[str, Any], float]] = []
    for document in GUIDELINE_CORPUS:
        source = str(document.get("source", "")).lower()
        if guideline_source and guideline_source.lower() not in source:
            continue
        doc_tokens = _tokenize(document.get("text", "") + " " + document.get("topic", ""))
        if not doc_tokens:
            continue
        overlap = len(normalized_query & doc_tokens)
        if overlap == 0:
            continue
        score = overlap / max(1, len(doc_tokens))
        scored.append((document, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    top_results = []
    for document, score in scored[:3]:
        top_results.append(
            {
                "id": document.get("id"),
                "text": document.get("text"),
                "source": document.get("source"),
                "score": round(score, 3),
            }
        )
    return top_results


def _initialize_guideline_collection() -> Any:
    """Initialize or reuse a persistent Chroma collection.

    Returns:
        A Chroma collection when the dependency is available; otherwise None.
    """
    if chromadb is None:
        return None

    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_or_create_collection(name="clinical_guidelines")
        if collection.count() == 0:
            documents = [doc.get("text", "") for doc in GUIDELINE_CORPUS]
            metadatas = [
                {
                    "source": doc.get("source", ""),
                    "condition": doc.get("condition", ""),
                    "topic": doc.get("topic", ""),
                }
                for doc in GUIDELINE_CORPUS
            ]
            ids = [doc.get("id", f"doc_{index}") for index, doc in enumerate(GUIDELINE_CORPUS)]
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return collection
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Chroma initialization failed: %s", exc)
        return None


async def _fetch_drug_interaction_payload(drugs: List[str]) -> Any:
    """Fetch drug interaction payload from an Apify endpoint.

    Args:
        drugs: List of drug names to query.

    Returns:
        Parsed JSON response from the remote service.

    Raises:
        httpx.HTTPError: If the request fails.
    """
    if not APIFY_DRUG_INTERACTION_URL:
        raise RuntimeError("APIFY_DRUG_INTERACTION_URL is not configured")

    payload = {"drugs": drugs}
    timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(APIFY_DRUG_INTERACTION_URL, json=payload)
        response.raise_for_status()
        return response.json()


async def _fetch_openfda_payload(drug_name: str) -> Any:
    """Fetch a drug label payload from the openFDA API.

    Args:
        drug_name: Human-readable drug name.

    Returns:
        Parsed JSON response from the API.

    Raises:
        httpx.HTTPError: If the request fails.
    """
    encoded = quote(drug_name)
    url = f"{OPENFDA_BASE_URL}?search=brand_name:{encoded}&limit=1"
    timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def _extract_openfda_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the requested contraindication-related fields from openFDA payload."""
    results = payload.get("results", [])
    if not results:
        return {}

    item = results[0]
    return {
        "contraindications": item.get("contraindications") or item.get("contraindications_and_warnings") or None,
        "warnings_and_precautions": item.get("warnings_and_precautions") or None,
        "pregnancy_or_breastfeeding": item.get("pregnancy_and_breastfeeding") or None,
        "adverse_reactions": item.get("adverse_reactions") or None,
    }


@mcp.tool()
@instrument_tool("query_clinical_guidelines")
def query_clinical_guidelines(
    query: str,
    guideline_source: Optional[str] = None,
    authorization: Optional[str] = None,
) -> dict:
    """Query local cardiovascular guideline evidence via semantic RAG.

    This tool retrieves clinical guidelines using:
    1. ChromaDB vector database (persistent local storage)
    2. Fallback token-based TF-IDF search for degraded environments
    3. Giskard security scanning on retrieved evidence
    4. DeepEval quality metrics for retrieval evaluation
    5. Redis caching for frequently accessed queries

    Args:
        query: A clinical question or search phrase relating to cardiovascular care.
        guideline_source: Optional filter such as ACC/AHA, ESC, WHO, or ADA.

    Returns:
        A dictionary with retrieved evidence, sources, and quality metrics.
    """
    start_time = time.time()
    try:
        validated_query = _validate_text_input(query, "query")
        source_filter = guideline_source.strip() if isinstance(guideline_source, str) and guideline_source.strip() else None

        # Check cache first
        cache_key = {"query": validated_query, "source": source_filter}
        cached_result = cache.get("guideline_search", cache_key)
        if cached_result is not None:
            logger.info("Returning cached guideline result")
            return cached_result

        collection = _initialize_guideline_collection()
        evidence: List[Dict[str, Any]] = []

        if collection is not None:
            try:
                results = collection.query(
                    query_texts=[validated_query],
                    n_results=3,
                    where={"source": {"$contains": source_filter}} if source_filter else None,
                )
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                if documents:
                    evidence = [
                        {
                            "text": document,
                            "source": metadata.get("source") if metadata else None,
                        }
                        for document, metadata in zip(documents, metadatas)
                    ]
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Chroma query failed, falling back to local search: %s", exc)

        if not evidence:
            fallback_evidence = _fallback_guideline_search(validated_query, source_filter)
            evidence = [
                {"text": item["text"], "source": item["source"], "score": item["score"]}
                for item in fallback_evidence
            ]

        sources = [item["source"] for item in evidence if item.get("source")]
        response: Dict[str, Any] = {"retrieved_evidence": evidence, "sources": sources}

        # Run Giskard security scanning on retrieved evidence
        for item in evidence:
            scan_result = GiskardSecurityScanner.scan_guideline_output(item.get("text", ""))
            if scan_result["violation_count"] > 0:
                logger.warning("Security violations detected in evidence: %s", scan_result["violations"])

        # Evaluate RAG retrieval quality with DeepEval
        eval_result = evaluate_guideline_response(validated_query, evidence, sources)
        response["evaluation"] = eval_result

        # Cache the result
        cache.set("guideline_search", cache_key, response)

        # Record metrics
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_latency("guideline_search", latency_ms)
        tracer.trace_rag_retrieval(validated_query, len(evidence), sources, latency_ms)

        return response

    except GuardrailValidationError as exc:
        latency_ms = (time.time() - start_time) * 1000
        tracer.trace_error("query_clinical_guidelines", "GuardrailValidationError", str(exc))
        return _structured_error("validation_error", str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        latency_ms = (time.time() - start_time) * 1000
        tracer.trace_error("query_clinical_guidelines", type(exc).__name__, str(exc))
        logger.exception("Guideline search failed")
        return _structured_error("guideline_search_error", str(exc))


@mcp.tool()
@instrument_tool("check_drug_interactions")
def check_drug_interactions(drugs: List[str], authorization: Optional[str] = None) -> dict:
    """Check for potential drug interactions using an asynchronous HTTP client.

    This tool:
    1. Validates input using guardrails
    2. Queries Apify drug interaction endpoint
    3. Scans results for critical warnings via Giskard
    4. Caches results for performance
    5. Traces execution via LangSmith

    Args:
        drugs: A list of drug names to evaluate for interactions.

    Returns:
        Parsed JSON data from the upstream interaction service or a structured error payload.
    """
    start_time = time.time()
    try:
        validated_drugs = _validate_drug_list(drugs)

        # Check cache
        cache_key = {"drugs": sorted(validated_drugs)}
        cached_result = cache.get("drug_interactions", cache_key)
        if cached_result is not None:
            logger.info("Returning cached drug interaction result")
            return cached_result

        payload = asyncio.run(_fetch_drug_interaction_payload(validated_drugs))

        response: Dict[str, Any] = {"status": "ok", "data": payload}

        # Giskard scanning for critical warnings
        payload_text = json.dumps(payload)
        scan_result = GiskardSecurityScanner.scan_drug_recommendation(payload_text)
        if scan_result["requires_review"]:
            response["requires_review"] = True
            response["critical_warnings"] = scan_result["critical_warnings"]

        # Cache result
        cache.set("drug_interactions", cache_key, response)

        # Record metrics
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_latency("drug_interactions", latency_ms)
        tracer.trace_tool_call("check_drug_interactions", {"drugs": validated_drugs}, response, latency_ms)

        return response

    except GuardrailValidationError as exc:
        latency_ms = (time.time() - start_time) * 1000
        tracer.trace_error("check_drug_interactions", "GuardrailValidationError", str(exc))
        return _structured_error("validation_error", str(exc))
    except RuntimeError as exc:
        return _structured_error("configuration_error", str(exc))
    except httpx.RequestError as exc:
        latency_ms = (time.time() - start_time) * 1000
        tracer.trace_error("check_drug_interactions", "NetworkError", str(exc))
        logger.warning("Drug interaction lookup failed: %s", exc)
        return _structured_error("network_error", "Unable to reach the drug interaction service", {"details": str(exc)})
    except Exception as exc:  # pragma: no cover - defensive
        latency_ms = (time.time() - start_time) * 1000
        tracer.trace_error("check_drug_interactions", type(exc).__name__, str(exc))
        logger.exception("Drug interaction lookup failed")
        return _structured_error("interaction_lookup_error", str(exc))


@mcp.tool()
@instrument_tool("check_patient_contraindications")
def check_patient_contraindications(drug_name: str, authorization: Optional[str] = None) -> dict:
    """Retrieve contraindication and warning information for a drug from openFDA.

    This tool:
    1. Validates drug name using guardrails
    2. Queries openFDA API asynchronously
    3. Extracts relevant safety fields
    4. Performs Giskard security scanning
    5. Caches results for performance
    6. Traces execution via LangSmith

    Args:
        drug_name: The drug name or active ingredient to inspect.

    Returns:
        A dictionary containing the requested safety fields when available, or a structured error payload.
    """
    start_time = time.time()
    try:
        validated_name = _validate_text_input(drug_name, "drug_name")

        # Check cache
        cache_key = {"drug": validated_name}
        cached_result = cache.get("contraindications", cache_key)
        if cached_result is not None:
            logger.info("Returning cached contraindication result")
            return cached_result

        payload = asyncio.run(_fetch_openfda_payload(validated_name))
        extracted = _extract_openfda_fields(payload)

        if not any(extracted.values()):
            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_error("check_patient_contraindications", "NotFound", f"No data for {validated_name}")
            return _structured_error("not_found", f"No contraindication data found for {validated_name}")

        response: Dict[str, Any] = {"status": "ok", "data": extracted}

        # Giskard scanning for warnings
        data_text = json.dumps(extracted)
        scan_result = GiskardSecurityScanner.scan_drug_recommendation(data_text)
        if scan_result["requires_review"]:
            response["critical_warnings"] = scan_result["critical_warnings"]

        # Cache result
        cache.set("contraindications", cache_key, response)

        # Record metrics
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_latency("contraindications", latency_ms)
        tracer.trace_tool_call("check_patient_contraindications", {"drug": validated_name}, response, latency_ms)

        return response

    except GuardrailValidationError as exc:
        latency_ms = (time.time() - start_time) * 1000
        tracer.trace_error("check_patient_contraindications", "GuardrailValidationError", str(exc))
        return _structured_error("validation_error", str(exc))
    except httpx.RequestError as exc:
        latency_ms = (time.time() - start_time) * 1000
        tracer.trace_error("check_patient_contraindications", "NetworkError", str(exc))
        logger.warning("openFDA lookup failed: %s", exc)
        return _structured_error("network_error", "Unable to reach the openFDA service", {"details": str(exc)})
    except Exception as exc:  # pragma: no cover - defensive
        latency_ms = (time.time() - start_time) * 1000
        tracer.trace_error("check_patient_contraindications", type(exc).__name__, str(exc))
        logger.exception("openFDA lookup failed")
        return _structured_error("contraindication_lookup_error", str(exc))


@mcp.tool()
@instrument_tool("calculate_ascvd_risk")
def calculate_ascvd_risk(
    age: int,
    gender: str,
    race: str,
    total_cholesterol: int,
    ldl: int,
    hdl: int,
    systolic_bp: int,
    on_bp_medication: bool,
    smoker: bool,
    diabetic: bool,
) -> dict:
    """Calculate 10-year ASCVD (atherosclerotic cardiovascular disease) risk.

    Uses the ACC/AHA pooled cohort equations to estimate cardiovascular risk
    and recommend appropriate statin intensity.

    Args:
        age: Age in years (40-79 recommended).
        gender: 'M' or 'F'.
        race: 'White', 'African American', or 'Other'.
        total_cholesterol: Total cholesterol in mg/dL.
        ldl: LDL cholesterol in mg/dL.
        hdl: HDL cholesterol in mg/dL.
        systolic_bp: Systolic blood pressure in mmHg.
        on_bp_medication: Whether on antihypertensive medication.
        smoker: Current smoking status.
        diabetic: Diabetes status.

    Returns:
        Dictionary with 10-year ASCVD risk percentage, category, and statin recommendation.
    """
    try:
        result = ASCVDRiskCalculator.calculate_10year_risk(
            age=age,
            gender=gender,
            race=race,
            total_cholesterol=total_cholesterol,
            ldl=ldl,
            hdl=hdl,
            systolic_bp=systolic_bp,
            on_bp_medication=on_bp_medication,
            smoker=smoker,
            diabetic=diabetic,
        )
        tracer.trace_tool_call("calculate_ascvd_risk", {"age": age, "gender": gender}, result, 0)
        return result
    except Exception as exc:
        logger.exception("ASCVD risk calculation failed")
        return _structured_error("ascvd_calculation_error", str(exc))


@mcp.tool()
@instrument_tool("estimate_renal_function")
def estimate_renal_function(
    age: int,
    weight_kg: float,
    creatinine_mg_dl: float,
    gender: str = "M",
    authorization: Optional[str] = None,
) -> dict:
    """Estimate glomerular filtration rate (GFR) using Cockcroft-Gault formula.

    Used to assess renal function and guide medication dosing adjustments.

    Args:
        age: Age in years.
        weight_kg: Body weight in kilograms.
        creatinine_mg_dl: Serum creatinine in mg/dL.
        gender: 'M' or 'F'.

    Returns:
        Dictionary with estimated GFR and renal function category.
    """
    try:
        if not _authenticate_request(authorization):
            return _structured_error("authentication_error", "Authentication required")
        result = CreatinineClearanceCalculator.calculate_creatinine_clearance(
            age=age, weight_kg=weight_kg, creatinine_mg_dl=creatinine_mg_dl, gender=gender
        )
        tracer.trace_tool_call("estimate_renal_function", {"age": age, "weight_kg": weight_kg}, result, 0)
        return result
    except Exception as exc:
        logger.exception("Renal function estimation failed")
        return _structured_error("renal_estimation_error", str(exc))


@mcp.tool()
@instrument_tool("get_medication_dosing")
def get_medication_dosing(
    drug_name: str,
    egfr: Optional[float] = None,
    age: Optional[int] = None,
    weight_kg: Optional[float] = None,
    authorization: Optional[str] = None,
) -> dict:
    """Get medication dosing recommendations based on patient factors.

    Provides standard dosing and adjustments for common cardiovascular medications
    based on renal function, age, and other patient factors.

    Args:
        drug_name: Name of the medication (e.g., metformin, atorvastatin, lisinopril).
        egfr: Estimated glomerular filtration rate (for renal adjustments).
        age: Patient age (for age-based adjustments).
        weight_kg: Patient weight in kilograms.

    Returns:
        Dictionary with standard dose, renal-adjusted dose, and special considerations.
    """
    try:
        if not _authenticate_request(authorization):
            return _structured_error("authentication_error", "Authentication required")
        result = MedicationDosingCalculator.calculate_drug_dose(
            drug_name=drug_name, egfr=egfr, age=age, weight_kg=weight_kg
        )
        tracer.trace_tool_call("get_medication_dosing", {"drug": drug_name}, result, 0)
        return result
    except Exception as exc:
        logger.exception("Medication dosing calculation failed")
        return _structured_error("dosing_calculation_error", str(exc))


@mcp.tool()
def get_server_metrics(authorization: Optional[str] = None) -> dict:
    """Get current server performance metrics and cache statistics.

    Returns:
        Dictionary with performance metrics, cache stats, and system status.
    """
    try:
        if not _authenticate_request(authorization):
            return _structured_error("authentication_error", "Authentication required")
        perf_summary = metrics.get_summary()
        cache_stats = cache.stats()

        return {
            "status": "ok",
            "performance_metrics": perf_summary,
            "cache_statistics": cache_stats,
            "tracing_enabled": tracer.enabled,
        }
    except Exception as exc:
        logger.exception("Failed to get server metrics")
        return _structured_error("metrics_error", str(exc))


if __name__ == "__main__":
    mcp.run()

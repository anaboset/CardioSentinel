"""FastAPI application for CardioSentinel MAS."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator
import os

from utils.logging_setup import init_app_environment
from core.dependencies import get_container, require_api_auth
from core.graph import run_workflow
from core.serialization import state_to_dict
from security.validation import ValidationError, validate_patient_input

logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"
START_TIME = datetime.now()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_app_environment()
    logger.info("CardioSentinel API started (v%s)", APP_VERSION)
    yield
    logger.info("CardioSentinel API shutting down")


app = FastAPI(
    title="CardioSentinel MAS API",
    description="Multi-agent cardiovascular clinical decision support system",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PatientData(BaseModel):
    age: int = Field(..., ge=18, le=120)
    bp: str = Field(..., pattern=r"^\d{2,3}/\d{2,3}$")
    ldl: float = Field(..., ge=0, le=500)
    conditions: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    sex: str = Field(default="Male")
    hdl: Optional[float] = Field(default=None, ge=10, le=150)
    total_cholesterol: Optional[float] = Field(default=None, ge=100, le=400)
    on_bp_medication: Optional[bool] = False

    @model_validator(mode="before")
    @classmethod
    def sanitize_patient_payload(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        cleaned, _ = validate_patient_input(values)
        return cleaned


class AnalyzeRequest(BaseModel):
    patient: PatientData
    query: str = Field(..., min_length=3, max_length=1000)

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class HumanDecisionRequest(BaseModel):
    checkpoint_agent: str
    decision: str = Field(..., pattern=r"^(approved|rejected|needs_modification)$")
    decided_by: str = "clinician"
    rationale: str = ""


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    uptime = (datetime.now() - START_TIME).total_seconds()
    groq_configured = bool(os.getenv("GROQ_API_KEY"))
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "uptime_seconds": round(uptime, 1),
        "services": {
            "groq_llm": "configured" if groq_configured else "missing_api_key",
            "rag_engine": "ready",
            "openfda": "ready",
        },
    }


@app.post("/api/v1/analyze")
async def analyze_patient(request: AnalyzeRequest, auth: None = Depends(require_api_auth)):
    """
    Run the full CardioSentinel multi-agent analysis workflow.
    Returns structured clinical decision support output.
    """
    try:
        patient_dict, _ = validate_patient_input(request.patient.model_dump())
        logger.info(
            "Analysis request: age=%d, query='%s'",
            patient_dict["age"],
            request.query[:50],
        )
        state = run_workflow(patient_dict, request.query)
        result = state_to_dict(state)

        if state.workflow_status == "failed":
            raise HTTPException(
                status_code=422,
                detail={
                    "message": state.error_message or "Workflow failed",
                    "partial_result": result,
                },
            )

        return {"status": "success", "data": result}

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/api/v1/guidelines/search")
async def search_guidelines(q: str, conditions: str = "", auth: None = Depends(require_api_auth)):
    """Search guideline corpus directly."""
    container = get_container()

    cond_list = [c.strip() for c in conditions.split(",") if c.strip()]
    engine = container.create_guideline_engine()
    results = engine.search(q, cond_list)
    return {
        "query": q,
        "conditions": cond_list,
        "results": [
            {"text": doc["text"], "source": doc["source"], "score": round(score, 3)}
            for doc, score in results
        ],
    }


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_ui():
        return FileResponse(os.path.join(static_dir, "index.html"))

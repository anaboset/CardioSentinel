"""Shared runtime dependencies for the clinical MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from services.langsmith_tracing import LangSmithTracer, PerformanceMetrics
from services.redis_cache import get_cache


@dataclass
class ClinicalRuntime:
    """Container for observability and cache dependencies used by the MCP server."""

    tracer: LangSmithTracer
    metrics: PerformanceMetrics
    cache: object
    request_timeout_seconds: float
    auth_required: bool
    auth_token: Optional[str]


def get_runtime() -> ClinicalRuntime:
    """Build or reuse the shared MCP runtime configuration."""
    return ClinicalRuntime(
        tracer=LangSmithTracer(),
        metrics=PerformanceMetrics(),
        cache=get_cache(),
        request_timeout_seconds=float(os.getenv("CLINICAL_MCP_TIMEOUT_SECONDS", "10")),
        auth_required=os.getenv("AUTH_REQUIRED", "false").lower() == "true",
        auth_token=os.getenv("AUTH_TOKEN", "").strip(),
    )

"""Dependency injection helpers for agents, tools, and services."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Optional

from fastapi import HTTPException, Request

from services.redis_cache import get_cache


class AuthProvider:
    """Simple bearer-token auth provider for API and MCP endpoints."""

    def __init__(self, required: Optional[bool] = None, token: Optional[str] = None):
        self.required = required if required is not None else os.getenv("AUTH_REQUIRED", "false").lower() == "true"
        self.expected_token = (token or os.getenv("AUTH_TOKEN", "")).strip()

    def is_enabled(self) -> bool:
        return self.required and bool(self.expected_token)

    def validate(self, provided_token: Optional[str]) -> None:
        if not self.is_enabled():
            return

        token = (provided_token or "").strip()
        if token != self.expected_token:
            raise HTTPException(status_code=401, detail="Authentication required")

    def validate_request(self, request: Request) -> None:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer", "", 1).strip() if auth_header else None
        self.validate(token)


class ServiceContainer:
    """Container for constructing agents/tools with injectable dependencies."""

    def __init__(self, auth_provider: Optional[AuthProvider] = None, cache: Optional[Any] = None):
        self.auth_provider = auth_provider or AuthProvider()
        self.cache = cache or get_cache()

    def create_guideline_engine(self):
        from services.rag_engine import RAGEngine

        return RAGEngine(cache=self.cache)

    def create_guideline_tool(self):
        from tools.rag_tool import GuidelineRetrieverTool

        return GuidelineRetrieverTool(engine=self.create_guideline_engine())

    def create_risk_tool(self):
        from tools.risk_tool import RiskScoreCalculator

        return RiskScoreCalculator()

    def create_interaction_tool(self):
        from tools.interaction_tool import DrugInteractionTool

        return DrugInteractionTool(cache=self.cache)

    def create_contraindication_tool(self):
        from tools.contraindication_tool import ContraindicationChecker

        return ContraindicationChecker(cache=self.cache)

    def create_guideline_agent(self):
        from agents.guideline_agent import GuidelineAgent

        return GuidelineAgent(tool=self.create_guideline_tool())

    def create_risk_agent(self):
        from agents.risk_agent import RiskAgent

        return RiskAgent(tool=self.create_risk_tool())

    def create_medication_agent(self):
        from agents.medication_agent import MedicationAgent

        return MedicationAgent(
            interaction_tool=self.create_interaction_tool(),
            contraindication_tool=self.create_contraindication_tool(),
        )

    def create_patient_agent(self):
        from agents.patient_agent import PatientAgent

        return PatientAgent(dependencies=self)


@lru_cache(maxsize=1)
def get_container() -> ServiceContainer:
    return ServiceContainer()


def require_api_auth(request: Request) -> None:
    container = get_container()
    container.auth_provider.validate_request(request)

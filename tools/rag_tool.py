"""Guideline retrieval tool using semantic RAG engine."""

import logging

from core.base import BaseTool

logger = logging.getLogger(__name__)


class GuidelineRetrieverTool(BaseTool):
    """Retrieves evidence-based guidelines via semantic RAG search."""

    def __init__(self, engine=None):
        super().__init__("guideline_retriever")
        self._engine = engine
        if self._engine is None:
            from services.rag_engine import RAGEngine

            self._engine = RAGEngine()

    def run(self, patient_summary: dict, clinical_question: str) -> dict:
        logger.info("[RAGTool] Query: %s", clinical_question)

        def _retrieve():
            return self._engine.retrieve(patient_summary, clinical_question)

        try:
            return self.execute_with_retry(_retrieve)
        except Exception as exc:
            logger.error("[RAGTool] Retrieval failed after retries: %s", exc)
            return {
                "status": "insufficient_evidence",
                "recommendations": [],
                "sources": [],
            }
import logging
from schemas.outputs import GuidelineOutput

logger = logging.getLogger(__name__)


class GuidelineAgent:
    """Retrieves evidence-grounded treatment guidelines via RAG."""

    def __init__(self, tool=None):
        self.tool = tool
        if self.tool is None:
            from tools.rag_tool import GuidelineRetrieverTool

            self.tool = GuidelineRetrieverTool()

    def run(self, patient: dict, query: str) -> GuidelineOutput:
        """Run the guideline agent and return structured output."""
        logger.info("[GuidelineAgent] Fetching guidelines...")
        try:
            result = self.tool.run(patient_summary=patient, clinical_question=query)

            if result["status"] == "insufficient_evidence":
                return GuidelineOutput(
                    recommendations=["insufficient_evidence"],
                    evidence_sources=[],
                    confidence="none",
                )

            return GuidelineOutput(
                recommendations=result["recommendations"],
                evidence_sources=result["sources"],
                confidence=result.get("confidence", "moderate"),
            )

        except Exception as e:
            logger.error(f"[GuidelineAgent] Tool failed: {e}")
            return GuidelineOutput(
                recommendations=["insufficient_evidence"],
                evidence_sources=[],
                confidence="none",
            )
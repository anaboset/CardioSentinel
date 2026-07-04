import logging
from schemas.outputs import RiskOutput

logger = logging.getLogger(__name__)


class RiskAgent:
    """Calculates and classifies cardiovascular risk."""

    def __init__(self, tool=None):
        self.tool = tool
        if self.tool is None:
            from tools.risk_tool import RiskScoreCalculator

            self.tool = RiskScoreCalculator()

    def run(self, patient: dict) -> RiskOutput:
        """Run the risk agent and return structured output."""
        logger.info("[RiskAgent] Calculating risk...")
        try:
            result = self.tool.run(patient)
            return RiskOutput(
                score=result["score"],
                classification=result["classification"],
                factors=result["factors"],
            )
        except Exception as e:
            logger.error(f"[RiskAgent] Tool failed: {e}")
            return RiskOutput(score=0.0, classification="Unknown", factors=[])
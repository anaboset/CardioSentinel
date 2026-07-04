"""Conditional edge routing for LangGraph."""

import logging
from typing import Literal

from config import RISK_THRESHOLDS
from schemas.state import WorkflowState

logger = logging.getLogger(__name__)


def create_edge_functions():
    """Create all edge routing functions for the graph."""

    def route_after_risk(state: WorkflowState) -> Literal["medication", "patient", "human_review"]:
        """Route after risk assessment — always proceed to medication check."""
        logger.info("[RouteAfterRisk] Determining next step...")

        if not state.risk:
            logger.info("[RouteAfterRisk] No risk assessment, skipping medication check")
            return "patient"

        if state.risk.score >= RISK_THRESHOLDS["very_high"]:
            logger.info(
                "[RouteAfterRisk] Very high risk (%.1f%%) — flagging for HITL after full workup",
                state.risk.score,
            )
            state.human_review_needed = True

        logger.info("[RouteAfterRisk] Routing to medication safety check")
        return "medication"

    def route_after_medication(state: WorkflowState) -> Literal["patient", "human_review", "proceed"]:
        """Route after medication safety check — always proceed to patient communication."""
        logger.info("[RouteAfterMedication] Determining next step...")

        if not state.medication_safety:
            logger.info("[RouteAfterMedication] No medication check performed")
            return "patient"

        if not state.medication_safety.safe_to_proceed:
            logger.warning(
                "[RouteAfterMedication] Safety concerns found, flagging for HITL review"
            )
            state.human_review_needed = True

        logger.info("[RouteAfterMedication] Proceeding to patient communication")
        return "patient"

    def route_after_review(state: WorkflowState) -> Literal["approved", "rejected", "needs_modification", "skip_review"]:
        """Route after human review."""
        logger.info("[RouteAfterReview] Processing human review decision...")

        if not state.human_decisions:
            logger.info("[RouteAfterReview] No human decisions recorded, completing workflow")
            return "skip_review"

        latest_decision = state.human_decisions[-1]

        if latest_decision.decision == "approved":
            logger.info("[RouteAfterReview] Approved by human, finalizing report")
            return "approved"
        elif latest_decision.decision == "rejected":
            logger.info("[RouteAfterReview] Rejected by human, ending workflow")
            return "rejected"
        elif latest_decision.decision == "needs_modification":
            logger.info("[RouteAfterReview] Human requested modifications, processing...")
            return "needs_modification"
        else:
            logger.info("[RouteAfterReview] Unknown decision, completing workflow")
            return "skip_review"

    return {
        "route_after_risk": route_after_risk,
        "route_after_medication": route_after_medication,
        "route_after_review": route_after_review,
    }

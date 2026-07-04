"""Node definitions for LangGraph orchestration."""

import logging
from datetime import datetime
from typing import Dict, Any

from schemas.state import WorkflowState, ExecutionMetadata
from security.validation import validate_patient_input, validate_query, ValidationError
from core.dependencies import get_container

logger = logging.getLogger(__name__)


def create_node_functions() -> Dict[str, Any]:
    """Create all node functions for the graph."""

    def input_validation(state: WorkflowState) -> WorkflowState:
        """Validate and sanitize input data."""
        logger.info("[InputValidation] Starting input validation...")

        try:
            if not state.patient_data:
                raise ValidationError("Patient data is required")
            if not state.query:
                raise ValidationError("Query is required")

            cleaned_query = validate_query(state.query)
            cleaned_patient, warnings = validate_patient_input(state.patient_data)

            state.patient_data = cleaned_patient
            state.query = cleaned_query

            metadata = {"warnings": warnings} if warnings else {}
            state.add_audit_entry(
                "input_validation",
                "validated",
                f"Validated input for query: {state.query}",
                metadata,
            )
            logger.info("[InputValidation] Input validation passed")

        except ValidationError as e:
            logger.error("[InputValidation] Validation failed: %s", e)
            state.mark_failed(f"Input validation error: {e}")
        except Exception as e:
            logger.error("[InputValidation] Unexpected error: %s", e)
            state.mark_failed(f"Input validation error: {e}")

        return state

    def _should_skip(state: WorkflowState) -> bool:
        """Check if workflow should skip remaining agents due to failure."""
        return state.workflow_status == "failed"
    
    def guideline_agent_node(state: WorkflowState) -> WorkflowState:
        """Run guideline agent."""
        if _should_skip(state):
            return state
        logger.info("[GuidelineNode] Running guideline agent...")
        
        try:
            agent = get_container().create_guideline_agent()
            result = agent.run(state.patient_data, state.query)
            state.guidelines = result
            
            state.add_audit_entry(
                "guideline_agent",
                "executed",
                f"Retrieved {len(result.recommendations)} recommendations",
                {"confidence": result.confidence},
            )
            logger.info("[GuidelineNode] ✓ Guideline agent completed")
            
        except Exception as e:
            logger.error(f"[GuidelineNode] Error: {e}")
            state.add_audit_entry("guideline_agent", "failed", str(e))
        
        return state
    
    def risk_agent_node(state: WorkflowState) -> WorkflowState:
        """Run risk agent."""
        if _should_skip(state):
            return state
        logger.info("[RiskNode] Running risk agent...")
        
        try:
            agent = get_container().create_risk_agent()
            result = agent.run(state.patient_data)
            state.risk = result
            
            state.add_audit_entry(
                "risk_agent",
                "executed",
                f"Calculated risk: {result.classification} (Score: {result.score})",
                {"score": result.score, "classification": result.classification},
            )
            logger.info("[RiskNode] ✓ Risk agent completed")
            
        except Exception as e:
            logger.error(f"[RiskNode] Error: {e}")
            state.add_audit_entry("risk_agent", "failed", str(e))
        
        return state
    
    def medication_agent_node(state: WorkflowState) -> WorkflowState:
        """Run medication agent."""
        if _should_skip(state):
            return state
        logger.info("[MedicationNode] Running medication agent...")
        
        try:
            agent = get_container().create_medication_agent()
            result = agent.run(state.patient_data)
            state.medication_safety = result
            
            state.add_audit_entry(
                "medication_agent",
                "executed",
                f"Safety check: {'SAFE' if result.safe_to_proceed else 'UNSAFE'}",
                {
                    "safe": result.safe_to_proceed,
                    "interactions": len(result.interactions),
                    "contraindications": len(result.contraindications),
                },
            )
            logger.info("[MedicationNode] ✓ Medication agent completed")
            
        except Exception as e:
            logger.error(f"[MedicationNode] Error: {e}")
            state.add_audit_entry("medication_agent", "failed", str(e))
        
        return state
    
    def patient_agent_node(state: WorkflowState) -> WorkflowState:
        """Run patient agent."""
        if _should_skip(state):
            return state
        logger.info("[PatientNode] Running patient agent...")
        
        try:
            if not state.guidelines or not state.risk:
                logger.warning("[PatientNode] Missing prerequisites for patient agent")
                return state
            
            agent = get_container().create_patient_agent()
            result = agent.run(state.patient_data, state.guidelines, state.risk)
            state.patient_communication = result
            
            state.add_audit_entry(
                "patient_agent",
                "executed",
                "Generated patient communication",
                {"advice_count": len(result.lifestyle_advice)},
            )
            logger.info("[PatientNode] ✓ Patient agent completed")
            
        except Exception as e:
            logger.error(f"[PatientNode] Error: {e}")
            state.add_audit_entry("patient_agent", "failed", str(e))
        
        return state
    
    def human_review_node(state: WorkflowState) -> WorkflowState:
        """Placeholder for human review checkpoint."""
        logger.info("[HumanReview] Requesting human review...")
        state.workflow_status = "reviewing"
        state.human_review_needed = True
        state.add_audit_entry(
            "human_review",
            "initiated",
            "Awaiting human approval",
        )
        return state
    
    def process_modifications_node(state: WorkflowState) -> WorkflowState:
        """Process any modifications from human review."""
        logger.info("[ProcessModifications] Processing human modifications...")
        
        if not state.human_decisions:
            logger.warning("[ProcessModifications] No human decisions to process")
            return state
        
        latest_decision = state.human_decisions[-1]
        
        if latest_decision.modifications:
            logger.info(f"[ProcessModifications] Applying {len(latest_decision.modifications)} modifications")
            state.add_audit_entry(
                "process_modifications",
                "applied",
                f"Applied {len(latest_decision.modifications)} modifications",
            )
        
        return state
    
    def finalize_report_node(state: WorkflowState) -> WorkflowState:
        """Finalize the report."""
        logger.info("[FinalizeReport] Finalizing report...")
        state.workflow_status = "completed"
        state.add_audit_entry(
            "finalize_report",
            "completed",
            "Report finalized",
        )
        return state
    
    return {
        "input_validation": input_validation,
        "guideline_agent": guideline_agent_node,
        "risk_agent": risk_agent_node,
        "medication_agent": medication_agent_node,
        "patient_agent": patient_agent_node,
        "human_review": human_review_node,
        "process_modifications": process_modifications_node,
        "finalize_report": finalize_report_node,
    }
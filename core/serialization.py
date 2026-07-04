"""Serialize WorkflowState to API-friendly dict."""

from dataclasses import asdict
from typing import Any, Dict

from schemas.state import WorkflowState


def state_to_dict(state: WorkflowState) -> Dict[str, Any]:
    """Convert WorkflowState to a JSON-serializable dictionary."""

    def _serialize(obj: Any) -> Any:
        if obj is None:
            return None
        if hasattr(obj, "__dataclass_fields__"):
            return {k: _serialize(v) for k, v in asdict(obj).items()}
        if isinstance(obj, list):
            return [_serialize(i) for i in obj]
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return obj

    result = {
        "patient_data": state.patient_data,
        "query": state.query,
        "workflow_status": state.workflow_status,
        "error_message": state.error_message,
        "human_review_needed": state.human_review_needed,
        "guidelines": _serialize(state.guidelines),
        "risk": _serialize(state.risk),
        "medication_safety": _serialize(state.medication_safety),
        "patient_communication": _serialize(state.patient_communication),
        "audit_trail": _serialize(state.audit_trail),
        "execution_metadata": _serialize(state.execution_metadata),
        "human_decisions": _serialize(state.human_decisions),
    }
    return result

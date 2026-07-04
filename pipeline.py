"""Pipeline entry point wrapping LangGraph workflow."""

from core.graph import run_workflow
from core.serialization import state_to_dict


def run_pipeline(patient_data: dict, query: str) -> dict:
    """
    Run the full CardioSentinel analysis pipeline.
    Returns a JSON-serializable result dictionary.
    """
    state = run_workflow(patient_data, query)
    result = state_to_dict(state)
    if state.error_message:
        result["error"] = state.error_message
    return result

"""LangGraph graph builder and orchestration logic."""

import logging
from datetime import datetime
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from config import AgentNames
from schemas.state import WorkflowState, ExecutionMetadata
from core.node_definitions import create_node_functions
from core.edge_routing import create_edge_functions

logger = logging.getLogger(__name__)


def build_cardiosentinel_graph():
    """Build the LangGraph orchestration graph."""
    
    graph = StateGraph(WorkflowState)
    
    # Create node functions
    node_funcs = create_node_functions()
    
    # Create edge functions
    edge_funcs = create_edge_functions()
    
    # Add nodes
    graph.add_node("input_validation", node_funcs["input_validation"])
    graph.add_node(AgentNames.GUIDELINE.value, node_funcs["guideline_agent"])
    graph.add_node(AgentNames.RISK.value, node_funcs["risk_agent"])
    graph.add_node(AgentNames.MEDICATION.value, node_funcs["medication_agent"])
    graph.add_node(AgentNames.PATIENT.value, node_funcs["patient_agent"])
    graph.add_node("human_review", node_funcs["human_review"])
    graph.add_node("process_modifications", node_funcs["process_modifications"])
    graph.add_node("finalize_report", node_funcs["finalize_report"])
    
    # Add edges with conditional routing
    graph.add_edge(START, "input_validation")
    
    graph.add_edge("input_validation", AgentNames.GUIDELINE.value)
    
    graph.add_edge(AgentNames.GUIDELINE.value, AgentNames.RISK.value)
    
    graph.add_conditional_edges(
        AgentNames.RISK.value,
        edge_funcs["route_after_risk"],
        {
            "medication": AgentNames.MEDICATION.value,
            "patient": AgentNames.PATIENT.value,
            "human_review": "human_review",
        }
    )
    
    graph.add_conditional_edges(
        AgentNames.MEDICATION.value,
        edge_funcs["route_after_medication"],
        {
            "patient": AgentNames.PATIENT.value,
            "human_review": "human_review",
            "proceed": AgentNames.PATIENT.value,
        }
    )
    
    graph.add_edge(AgentNames.PATIENT.value, "human_review")
    
    graph.add_conditional_edges(
        "human_review",
        edge_funcs["route_after_review"],
        {
            "approved": "finalize_report",
            "rejected": END,
            "needs_modification": "process_modifications",
            "skip_review": "finalize_report",
        }
    )
    
    graph.add_edge("process_modifications", "finalize_report")
    graph.add_edge("finalize_report", END)
    
    return graph.compile()


def create_initial_state(patient_data: dict, query: str) -> Dict[str, Any]:
    """Create initial workflow state as dict for LangGraph."""
    return {
        "patient_data": patient_data,
        "query": query,
        "workflow_status": "running",
        "audit_trail": [],
        "human_decisions": [],
        "execution_metadata": ExecutionMetadata(start_time=datetime.now()),
    }


def run_workflow(patient_data: dict, query: str) -> WorkflowState:
    """Run workflow synchronously."""
    
    graph = build_cardiosentinel_graph()
    
    try:
        logger.info(f"Starting CardioSentinel workflow for query: {query}")
        logger.info(f"Patient: Age {patient_data.get('age')}, "
                    f"BP {patient_data.get('bp')}, "
                    f"LDL {patient_data.get('ldl')}")
        
        result = graph.invoke(create_initial_state(patient_data, query))
        
        # Convert result to WorkflowState if needed
        if isinstance(result, dict):
            state = WorkflowState(**result)
        else:
            state = result
        
        state.workflow_status = "completed"
        if state.execution_metadata:
            state.execution_metadata.end_time = datetime.now()
            state.execution_metadata.total_duration_ms = (
                (state.execution_metadata.end_time -
                 state.execution_metadata.start_time).total_seconds() * 1000
            )

        if state.error_message:
            state.workflow_status = "failed"

        logger.info("Workflow finished with status: %s", state.workflow_status)
        return state
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        state = WorkflowState(patient_data=patient_data, query=query)
        state.mark_failed(str(e))
        return state

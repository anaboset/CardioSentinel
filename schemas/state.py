"""LangGraph State definitions for workflow orchestration."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas.outputs import (
    GuidelineOutput,
    MedicationSafetyOutput,
    RiskOutput,
    PatientOutput,
)


@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: datetime
    agent: str
    action: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HumanDecision:
    """Record of a human approval/modification decision."""
    checkpoint_agent: str
    decision: str  # "approved", "rejected", "needs_modification", etc.
    decided_by: str  # User ID or "system"
    decided_at: datetime
    modifications: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    original_output: Dict[str, Any] = field(default_factory=dict)
    modified_output: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionMetadata:
    """Metadata about workflow execution."""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: float = 0.0
    agents_executed: List[str] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    retries_performed: Dict[str, int] = field(default_factory=dict)
    checkpoints_triggered: List[str] = field(default_factory=list)


@dataclass
class WorkflowState:
    """Complete workflow state for LangGraph."""
    # Input
    patient_data: dict
    query: str
    
    # Intermediate outputs from agents
    guidelines: Optional[GuidelineOutput] = None
    risk: Optional[RiskOutput] = None
    medication_safety: Optional[MedicationSafetyOutput] = None
    patient_communication: Optional[PatientOutput] = None
    
    # HITL workflow
    human_review_needed: bool = False
    human_decisions: List[HumanDecision] = field(default_factory=list)
    pending_checkpoint_agent: Optional[str] = None
    
    # Traceability
    audit_trail: List[AuditEntry] = field(default_factory=list)
    execution_metadata: Optional[ExecutionMetadata] = None
    
    # Error tracking
    error_message: Optional[str] = None
    workflow_status: str = "pending"  # pending, running, reviewing, completed, failed
    
    def add_audit_entry(self, agent: str, action: str, description: str, metadata: Dict = None):
        """Add entry to audit trail."""
        entry = AuditEntry(
            timestamp=datetime.now(),
            agent=agent,
            action=action,
            description=description,
            metadata=metadata or {},
        )
        self.audit_trail.append(entry)
    
    def add_human_decision(self, decision: HumanDecision):
        """Record human decision."""
        self.human_decisions.append(decision)
    
    def mark_failed(self, error_message: str):
        """Mark workflow as failed with error."""
        self.workflow_status = "failed"
        self.error_message = error_message

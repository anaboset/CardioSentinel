"""Human-in-the-Loop approval workflow management."""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from schemas.state import HumanDecision, WorkflowState

logger = logging.getLogger(__name__)


class ApprovalManager:
    """Manages human approval workflows and decisions."""
    
    def __init__(self):
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.completed_decisions: List[HumanDecision] = []
    
    def request_approval(
        self,
        checkpoint_id: str,
        agent_name: str,
        output_data: Dict[str, Any],
        required_fields: List[str] = None,
    ) -> Dict[str, Any]:
        """Create an approval request."""
        
        logger.info(f"[ApprovalMgr] Requesting approval for {agent_name}")
        
        approval_request = {
            "checkpoint_id": checkpoint_id,
            "agent_name": agent_name,
            "output_data": output_data,
            "required_fields": required_fields or [],
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
        
        self.pending_approvals[checkpoint_id] = approval_request
        return approval_request
    
    def approve(
        self,
        checkpoint_id: str,
        user_id: str = "clinician",
        rationale: str = "",
    ) -> HumanDecision:
        """Approve an output."""
        
        if checkpoint_id not in self.pending_approvals:
            raise ValueError(f"No pending approval with ID: {checkpoint_id}")
        
        approval = self.pending_approvals[checkpoint_id]
        
        decision = HumanDecision(
            checkpoint_agent=approval["agent_name"],
            decision="approved",
            decided_by=user_id,
            decided_at=datetime.now(),
            original_output=approval["output_data"],
            modified_output={},
            rationale=rationale,
        )
        
        self.completed_decisions.append(decision)
        del self.pending_approvals[checkpoint_id]
        
        logger.info(f"[ApprovalMgr] ✓ Approved {approval['agent_name']}")
        return decision
    
    def reject(
        self,
        checkpoint_id: str,
        user_id: str = "clinician",
        reason: str = "",
    ) -> HumanDecision:
        """Reject an output."""
        
        if checkpoint_id not in self.pending_approvals:
            raise ValueError(f"No pending approval with ID: {checkpoint_id}")
        
        approval = self.pending_approvals[checkpoint_id]
        
        decision = HumanDecision(
            checkpoint_agent=approval["agent_name"],
            decision="rejected",
            decided_by=user_id,
            decided_at=datetime.now(),
            original_output=approval["output_data"],
            rationale=reason,
        )
        
        self.completed_decisions.append(decision)
        del self.pending_approvals[checkpoint_id]
        
        logger.info(f"[ApprovalMgr] ✗ Rejected {approval['agent_name']}")
        return decision
    
    def request_modification(
        self,
        checkpoint_id: str,
        modifications: Dict[str, Any],
        user_id: str = "clinician",
        reason: str = "",
    ) -> HumanDecision:
        """Request modifications to an output."""
        
        if checkpoint_id not in self.pending_approvals:
            raise ValueError(f"No pending approval with ID: {checkpoint_id}")
        
        approval = self.pending_approvals[checkpoint_id]
        
        decision = HumanDecision(
            checkpoint_agent=approval["agent_name"],
            decision="needs_modification",
            decided_by=user_id,
            decided_at=datetime.now(),
            original_output=approval["output_data"],
            modifications=modifications,
            rationale=reason,
        )
        
        self.completed_decisions.append(decision)
        del self.pending_approvals[checkpoint_id]
        
        logger.info(f"[ApprovalMgr] ⚙️  Modifications requested for {approval['agent_name']}")
        return decision
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests."""
        return list(self.pending_approvals.values())
    
    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get complete audit trail of all decisions."""
        return [asdict(d) for d in self.completed_decisions]
    
    def has_pending_approvals(self) -> bool:
        """Check if there are pending approvals."""
        return len(self.pending_approvals) > 0


class AuditLogger:
    """Logs all decisions and actions for compliance."""
    
    def __init__(self):
        self.entries: List[Dict[str, Any]] = []
    
    def log_action(
        self,
        action_type: str,
        agent: str,
        details: Dict[str, Any],
        user_id: str = "system",
    ):
        """Log an action."""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "agent": agent,
            "user_id": user_id,
            "details": details,
        }
        
        self.entries.append(entry)
        logger.info(f"[AuditLog] [{action_type}] {agent}: {details}")
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all audit logs."""
        return self.entries
    
    def export_json(self) -> str:
        """Export audit trail as JSON."""
        return json.dumps(self.entries, indent=2, default=str)

"""New CLI entry point using LangGraph orchestration."""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.logging_setup import init_app_environment

init_app_environment()

logger = logging.getLogger(__name__)

from core.graph import run_workflow
from schemas.state import WorkflowState


def print_workflow_results(state: WorkflowState) -> None:
    """Pretty-print workflow results."""
    
    print("\n" + "=" * 70)
    print("🫀 CARDIOSENTINEL MAS — CLINICAL DECISION SUPPORT REPORT")
    print("=" * 70)
    
    # Query and patient info
    print(f"\n📋 QUERY: {state.query}")
    patient = state.patient_data
    print(f"👤 PATIENT:")
    print(f"   Age: {patient.get('age')} years old")
    print(f"   BP: {patient.get('bp')} mmHg")
    print(f"   LDL: {patient.get('ldl')} mg/dL")
    print(f"   Conditions: {', '.join(patient.get('conditions', ['None']))}")
    
    # Risk assessment
    if state.risk:
        print(f"\n⚠️  RISK STRATIFICATION")
        print(f"   Classification: {state.risk.classification}")
        print(f"   Score: {state.risk.score}/100")
        print(f"   Risk Factors:")
        for factor in state.risk.factors:
            print(f"      • {factor}")
    
    # Guidelines
    if state.guidelines:
        print(f"\n📚 CLINICAL GUIDELINES")
        print(f"   Confidence: {state.guidelines.confidence}")
        print(f"   Recommendations:")
        if state.guidelines.recommendations == ["insufficient_evidence"]:
            print(f"      ⚠️  Insufficient evidence found")
        else:
            for rec in state.guidelines.recommendations:
                print(f"      • {rec}")
        if state.guidelines.evidence_sources:
            print(f"   Sources:")
            for src in state.guidelines.evidence_sources:
                print(f"      [{src}]")
    
    # Medication safety
    if state.medication_safety:
        status = "✅ SAFE TO PROCEED" if state.medication_safety.safe_to_proceed else "🚨 SAFETY CONCERNS"
        print(f"\n💊 MEDICATION SAFETY: {status}")
        if state.medication_safety.interactions:
            print(f"   Interactions:")
            for interaction in state.medication_safety.interactions:
                print(f"      ⚡ {interaction}")
        if state.medication_safety.contraindications:
            print(f"   Contraindications:")
            for contraindication in state.medication_safety.contraindications:
                print(f"      🚫 {contraindication}")
        if not state.medication_safety.interactions and not state.medication_safety.contraindications:
            print(f"   ✓ No interactions or contraindications flagged")
    
    # Patient communication
    if state.patient_communication:
        print(f"\n🤝 PATIENT COMMUNICATION")
        print(f"   Summary:")
        print(f"      {state.patient_communication.summary}")
        if state.patient_communication.lifestyle_advice:
            print(f"   Lifestyle Advice:")
            for advice in state.patient_communication.lifestyle_advice:
                print(f"      → {advice}")
    
    # Audit trail
    if state.audit_trail:
        print(f"\n📋 AUDIT TRAIL ({len(state.audit_trail)} entries)")
        for entry in state.audit_trail[:5]:  # Show first 5
            print(f"   [{entry.agent}] {entry.action}: {entry.description}")
        if len(state.audit_trail) > 5:
            print(f"   ... and {len(state.audit_trail) - 5} more entries")
    
    # Execution metadata
    if state.execution_metadata:
        print(f"\n⏱️  EXECUTION METRICS")
        print(f"   Duration: {state.execution_metadata.total_duration_ms:.0f}ms")
        print(f"   Agents executed: {len(state.execution_metadata.agents_executed)}")
    
    # Status and errors
    print(f"\n✅ STATUS: {state.workflow_status.upper()}")
    if state.error_message:
        print(f"❌ ERROR: {state.error_message}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    # Example patient case
    patient = {
        "age": 65,
        "sex": "Male",
        "bp": "150/95",
        "ldl": 160,
        "conditions": ["hypertension", "smoking"],
        "medications": [],
    }
    
    query = "What is the first-line therapy for this patient?"
    
    print("\n🚀 Starting CardioSentinel workflow...")
    print(f"Patient: {patient['age']}yo, BP {patient['bp']}, LDL {patient['ldl']}")
    print(f"Query: {query}\n")
    
    # Run workflow
    state = run_workflow(patient, query)
    
    # Print results
    print_workflow_results(state)

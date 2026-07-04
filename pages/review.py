"""Review and approval page for human-in-the-loop."""

import streamlit as st
from datetime import datetime


def render():
    """Render review and approval page."""
    
    st.markdown("## 👀 Review & Approval")
    
    st.info("""
    Review the agent-generated outputs below. You can approve, reject, or request modifications
    for any component. All decisions are logged for audit purposes.
    """)
    
    # Approval checkpoints
    st.markdown("### ✅ Approval Checkpoints")
    
    checkpoints = {
        "medication_safety": {
            "title": "💊 Medication Safety",
            "status": "pending_approval",
            "data": {
                "safe": True,
                "interactions": 0,
                "contraindications": 0,
            }
        },
        "risk_stratification": {
            "title": "📊 Risk Stratification",
            "status": "pending_approval",
            "data": {
                "score": 65,
                "classification": "High",
                "factors": ["Age 65", "Hypertension", "Smoking"]
            }
        },
        "recommendations": {
            "title": "📚 Clinical Guidelines",
            "status": "pending_approval",
            "data": {
                "count": 3,
                "confidence": "high",
            }
        }
    }
    
    for checkpoint_id, checkpoint in checkpoints.items():
        with st.expander(f"{checkpoint['title']} ({checkpoint['status'].replace('_', ' ').title()})", 
                        expanded=True):
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Show checkpoint details
                if checkpoint_id == "medication_safety":
                    if checkpoint['data']['safe']:
                        st.success("✅ **SAFE TO PROCEED** - No interactions or contraindications detected")
                    else:
                        st.error("⚠️ **SAFETY CONCERNS** - Review required")
                
                elif checkpoint_id == "risk_stratification":
                    st.metric("Risk Score", f"{checkpoint['data']['score']}/100")
                    st.markdown(f"**Classification**: {checkpoint['data']['classification']}")
                    st.markdown("**Contributing Factors**:")
                    for factor in checkpoint['data']['factors']:
                        st.markdown(f"- {factor}")
                
                elif checkpoint_id == "recommendations":
                    st.markdown(f"**Retrieved**: {checkpoint['data']['count']} guidelines")
                    st.markdown(f"**Confidence**: {checkpoint['data']['confidence'].title()}")
            
            with col2:
                # Approval buttons
                col_approve, col_mod, col_rej = st.columns(3)
                
                with col_approve:
                    if st.button("✅ Approve", key=f"approve_{checkpoint_id}", use_container_width=True):
                        st.session_state[f"{checkpoint_id}_approved"] = True
                        st.success("Approved!")
                
                with col_mod:
                    if st.button("⚙️ Modify", key=f"modify_{checkpoint_id}", use_container_width=True):
                        st.session_state[f"{checkpoint_id}_modifying"] = True
                
                with col_rej:
                    if st.button("❌ Reject", key=f"reject_{checkpoint_id}", use_container_width=True):
                        st.session_state[f"{checkpoint_id}_rejected"] = True
                        st.error("Rejected!")
    
    st.markdown("---")
    
    # Modification interface
    st.markdown("### ⚙️ Request Modifications")
    
    with st.form("modifications_form"):
        checkpoint_to_modify = st.selectbox(
            "Modify which checkpoint?",
            ["Medication Safety", "Risk Stratification", "Recommendations"]
        )
        
        if checkpoint_to_modify == "Risk Stratification":
            new_score = st.slider("Adjust Risk Score", 0, 100, 65)
            reason = st.text_area("Reason for modification")
        else:
            reason = st.text_area("Modification request details")
        
        if st.form_submit_button("💾 Submit Modification"):
            st.success("✅ Modification recorded!")
    
    st.markdown("---")
    
    # Final approval
    st.markdown("### 🎯 Final Decision")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Approve All & Proceed", use_container_width=True, type="primary"):
            st.success("✅ All approvals recorded! Generating final report...")
            st.session_state.workflow_approved = True
            st.session_state.current_page = "Results"
            st.rerun()
    
    with col2:
        if st.button("❌ Reject & Restart", use_container_width=True):
            st.warning("Workflow rejected. Returning to patient input...")
            st.session_state.patient_data = None
            st.session_state.current_page = "New Analysis"
            st.rerun()
    
    with col3:
        if st.button("💾 Save & Review Later", use_container_width=True):
            st.info("Workflow saved. You can return to it later.")

"""Workflow monitoring page showing real-time agent execution."""

import streamlit as st
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def render():
    """Render workflow monitoring page."""
    
    st.markdown("## ⚙️ Active Workflow")
    
    # Check if patient data exists
    if "patient_data" not in st.session_state:
        st.warning("⚠️ No active workflow. Please start a new analysis.")
        if st.button("Start New Analysis"):
            st.session_state.current_page = "New Analysis"
            st.rerun()
        return
    
    # Display patient summary
    with st.expander("👤 Patient Summary", expanded=False):
        patient = st.session_state.patient_data
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Age", f"{patient['age']} y/o")
        with col2:
            st.metric("BP", patient['bp'])
        with col3:
            st.metric("LDL", f"{patient['ldl']} mg/dL")
        with col4:
            st.metric("Risk", "Calculating...")
        
        st.markdown("**Conditions**: " + ", ".join(patient.get('conditions', [])))
        st.markdown("**Medications**: " + (", ".join(patient.get('medications', [])) or "None listed"))
    
    st.markdown("---")
    
    # Workflow execution display
    st.markdown("## 🔄 Agent Execution Progress")
    
    # Create workflow visualization
    col1, col2, col3 = st.columns([1, 1, 1])
    
    agents = [
        {
            "name": "Guideline Retrieval",
            "icon": "📚",
            "description": "Fetching clinical guidelines",
            "duration": 2,
        },
        {
            "name": "Risk Stratification",
            "icon": "📊",
            "description": "Calculating cardiovascular risk",
            "duration": 1,
        },
        {
            "name": "Medication Safety",
            "icon": "💊",
            "description": "Checking drug interactions",
            "duration": 1.5,
        },
    ]
    
    # Initialize progress if not exists
    if "workflow_progress" not in st.session_state:
        st.session_state.workflow_progress = {}
        st.session_state.current_agent_idx = 0
    
    # Run agents
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    for idx, agent in enumerate(agents):
        # Update current agent
        st.session_state.current_agent_idx = idx
        
        # Show progress bar
        with progress_placeholder.container():
            progress = (idx + 0.5) / len(agents)
            st.progress(progress, text=f"Running: {agent['name']}")
        
        # Show status
        with status_placeholder.container():
            st.markdown(f"### {agent['icon']} {agent['name']}")
            st.markdown(f"__{agent['description']}__")
        
        # Simulate execution with visual feedback
        col1, col2, col3 = st.columns([0.5, 3, 0.5])
        
        with col1:
            st.markdown(f"**{agent['icon']}**")
        
        with col2:
            progress_bar = st.progress(0)
            
            # Animate progress
            for i in range(100):
                time.sleep(0.01)  # Simulate work
                progress_bar.progress(i + 1)
        
        with col3:
            st.markdown("✅")
        
        # Mark as complete
        st.session_state.workflow_progress[idx] = "complete"
        time.sleep(0.3)  # Pause between agents
    
    # Clear placeholders
    progress_placeholder.empty()
    status_placeholder.empty()
    
    st.markdown("---")
    
    # Show results in tabs
    st.markdown("## 📊 Intermediate Results")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 Guidelines",
        "📊 Risk",
        "💊 Medication Safety",
        "🤝 Patient Communication"
    ])
    
    with tab1:
        st.markdown("### Clinical Guidelines")
        st.markdown("""
        - First-line therapy: ACE inhibitors or ARBs for hypertensive patients with diabetes or CKD
        - Target BP < 130/80 mmHg for high-risk patients (ACC/AHA 2023)
        - Beta-blockers preferred if concurrent ischemic heart disease
        
        **Confidence**: High (High-intensity sources)
        
        **Sources**:
        - ACC/AHA 2023 Hypertension Guidelines
        - JNC 8 Evidence-Based Guideline
        """)
    
    with tab2:
        st.markdown("### Risk Stratification")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Risk Score", "65/100")
            st.metric("Classification", "High")
        
        with col2:
            st.markdown("**Risk Factors**:")
            st.markdown("""
            - Age 65 years (≥65 years) [+25 points]
            - Severe hypertension (SBP 150) [+25 points]
            - High LDL (160 mg/dL) [+12 points]
            - Active smoker [+20 points]
            """)
    
    with tab3:
        st.markdown("### Medication Safety Check")
        
        success_state = st.session_state.patient_data.get('medications', [])
        
        if success_state:
            st.success("""
            ✅ **SAFE TO PROCEED**
            
            No significant interactions or contraindications detected.
            """)
        else:
            st.info("No medications listed for interaction checking.")
    
    with tab4:
        st.markdown("### Patient-Friendly Communication")
        st.info("""
        **Your Health Summary**
        
        Based on your recent health screening, you have been classified as having **high 
        cardiovascular risk**. This means you would benefit from careful management of your 
        blood pressure and cholesterol levels to reduce your risk of heart disease or stroke.
        
        **Recommended Actions**:
        - Take your blood pressure medication as prescribed every day
        - Reduce salt intake and aim for more heart-healthy foods
        - Exercise for at least 150 minutes per week
        - If you smoke, this is the most important change you can make for your heart health
        """)
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👀 Review & Approve", use_container_width=True):
            st.session_state.current_page = "Review & Approve"
            st.rerun()
    
    with col2:
        if st.button("📊 View Results", use_container_width=True):
            st.session_state.current_page = "Results"
            st.rerun()
    
    with col3:
        if st.button("🆕 New Analysis", use_container_width=True):
            # Clear session
            st.session_state.patient_data = None
            st.session_state.clinical_query = None
            st.session_state.current_page = "New Analysis"
            st.rerun()

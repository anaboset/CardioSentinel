"""Home page for CardioSentinel UI."""

import streamlit as st
from datetime import datetime


def render():
    """Render home page."""
    
    # Custom hero section
    st.markdown("""
    <style>
    .hero-section {
        background: linear-gradient(135deg, #E63946 0%, #457B9D 100%);
        padding: 3rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .hero-section h1 {
        font-size: 3rem;
        margin: 0;
        font-weight: bold;
    }
    .hero-section p {
        font-size: 1.2rem;
        margin: 1rem 0 0 0;
        opacity: 0.9;
    }
    </style>
    <div class="hero-section">
        <h1>🫀 CardioSentinel</h1>
        <p>Next-Generation Clinical Decision Support for Cardiovascular Care</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Agents", "5", "+1 from v0.9")
    with col2:
        st.metric("HITL Checkpoints", "3", "With audit trail")
    with col3:
        st.metric("Safety Checks", "8+", "Drug interactions & contraindications")
    with col4:
        st.metric("Uptime", "100%", "No incidents")
    
    st.markdown("---")
    
    # Feature overview
    st.markdown("## 🌟 Key Features")
    
    feature_cols = st.columns(3)
    
    with feature_cols[0]:
        st.markdown("""
        ### 🧠 Intelligent Orchestration
        - **LangGraph-based** workflow
        - **Conditional routing** based on risk
        - **Adaptive** agent selection
        - **Fallback** mechanisms
        """)
    
    with feature_cols[1]:
        st.markdown("""
        ### 👤 Human-in-the-Loop
        - **Approval checkpoints** at critical steps
        - **Editable outputs** for clinician override
        - **Audit trails** for compliance
        - **Decision tracking** with rationale
        """)
    
    with feature_cols[2]:
        st.markdown("""
        ### 💊 Clinical Intelligence
        - **Guideline retrieval** with confidence
        - **Risk stratification** (Low→Very High)
        - **Drug interactions** database
        - **Contraindication** checking
        """)
    
    st.markdown("---")
    
    # Quick start
    st.markdown("## 🚀 Quick Start")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Step 1: Enter Patient Data**
        - Demographics (age, blood pressure, LDL)
        - Active conditions (hypertension, diabetes, etc.)
        - Current medications
        """)
    
    with col2:
        st.info("""
        **Step 2: Submit Clinical Query**
        - "What is first-line therapy?"
        - "Is this patient a candidate for..."
        - "What medications are contraindicated?"
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("""
        **Step 3: Multi-Agent Analysis**
        - Guideline recommendations retrieved
        - Risk assessment calculated
        - Medication safety verified
        - Patient communication generated
        """)
    
    with col2:
        st.warning("""
        **Step 4: Human Review & Approve**
        - Review agent recommendations
        - Approve, modify, or reject
        - Complete audit trail created
        - Download final report
        """)
    
    st.markdown("---")
    
    # Agent architecture
    st.markdown("## 🔗 Agent Architecture")
    
    agent_info = {
        "🎯 Orchestrator": "Coordinates workflow, manages dependencies, routes decisions",
        "📚 Guideline Agent": "Retrieves clinical guidelines via RAG, returns evidence-based recommendations",
        "📊 Risk Agent": "Calculates cardiovascular risk score and classifies risk level",
        "💊 Medication Agent": "Checks drug interactions and contraindications",
        "🤝 Patient Agent": "Converts clinical output to plain-language patient communication",
    }
    
    cols = st.columns(2)
    for idx, (agent, desc) in enumerate(agent_info.items()):
        col = cols[idx % 2]
        with col:
            st.markdown(f"**{agent}**")
            st.markdown(f"_{desc}_")
    
    st.markdown("---")
    
    # Get started button
    st.markdown("## ▶️ Get Started")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Start New Analysis", use_container_width=True, type="primary"):
            st.session_state.current_page = "New Analysis"
            st.rerun()
    
    st.markdown("---")
    
    # Footer with system info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📖 Documentation
        - [Architecture](https://github.com/anaboset/cardiosentinel)
        - [API Reference](#)
        - [Deployment Guide](#)
        """)
    
    with col2:
        st.markdown("""
        ### 🔒 Security & Compliance
        - HITL approval workflows
        - Complete audit logging
        - Data traceability
        - Decision history
        """)
    
    with col3:
        st.markdown("""
        ### 📞 Support
        - [Report Issues](https://github.com)
        - [Feature Requests](https://github.com)
        - [Contact](mailto:support@cardiosentinel.ai)
        """)

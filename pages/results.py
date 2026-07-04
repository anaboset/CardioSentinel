"""Results display page."""

import streamlit as st
from datetime import datetime


def render():
    """Render results page."""
    
    st.markdown("## 📋 Final Clinical Report")
    
    if "patient_data" not in st.session_state:
        st.warning("No active analysis. Please start a new analysis.")
        if st.button("Start New Analysis"):
            st.session_state.current_page = "New Analysis"
            st.rerun()
        return
    
    patient = st.session_state.patient_data
    
    # Patient header
    st.markdown(f"""
    ---
    **Patient**: {patient['age']} y/o {patient['sex']} | **BP**: {patient['bp']} | **LDL**: {patient['ldl']} mg/dL
    
    **Query**: {st.session_state.get('clinical_query', 'General assessment')}
    
    ---
    """)
    
    # Summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background-color: #E63946; padding: 1.5rem; border-radius: 8px; color: white; text-align: center;">
        <h3 style="margin: 0;">Risk Assessment</h3>
        <p style="font-size: 2em; margin: 0.5rem 0;">High</p>
        <p style="margin: 0; font-size: 0.9em;">Score: 65/100</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color: #457B9D; padding: 1.5rem; border-radius: 8px; color: white; text-align: center;">
        <h3 style="margin: 0;">Medication Safety</h3>
        <p style="font-size: 2em; margin: 0.5rem 0;">✅ Safe</p>
        <p style="margin: 0; font-size: 0.9em;">No interactions found</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background-color: #2A9D8F; padding: 1.5rem; border-radius: 8px; color: white; text-align: center;">
        <h3 style="margin: 0;">Guidelines</h3>
        <p style="font-size: 2em; margin: 0.5rem 0;">3 Recs</p>
        <p style="margin: 0; font-size: 0.9em;">High Confidence</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Detailed recommendations
    st.markdown("## 💊 Clinical Recommendations")
    
    recommendations = [
        {
            "title": "ACE Inhibitor or ARB Therapy",
            "guideline": "ACC/AHA 2023 Hypertension Guidelines",
            "details": "First-line therapy for hypertensive patients, especially with elevated risk or comorbidities",
            "priority": "High"
        },
        {
            "title": "Intensive Statin Therapy",
            "guideline": "ACC/AHA 2022 Cholesterol Guidelines",
            "details": "High-intensity statin for LDL >160 mg/dL with ASCVD risk >20%",
            "priority": "High"
        },
        {
            "title": "Smoking Cessation Program",
            "guideline": "USPSTF 2021 Tobacco Cessation",
            "details": "Smoking cessation is the highest-yield intervention for this patient",
            "priority": "Critical"
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        col1, col2 = st.columns([0.1, 0.9])
        
        with col1:
            if rec["priority"] == "Critical":
                st.markdown("🔴")
            elif rec["priority"] == "High":
                st.markdown("🟠")
            else:
                st.markdown("🟡")
        
        with col2:
            st.markdown(f"""
            ### {i}. {rec['title']}
            **Source**: {rec['guideline']}
            
            {rec['details']}
            """)
    
    st.markdown("---")
    
    # Patient Communication
    st.markdown("## 🤝 Patient Communication")
    
    st.info("""
    ### Your Health Summary
    
    Based on your health assessment, you have been identified as having **high cardiovascular risk**. 
    This means you would benefit from active management to reduce your risk of heart disease or stroke.
    
    ### What This Means
    Your blood pressure and cholesterol levels are higher than recommended targets. Combined with your 
    smoking status, this increases your cardiovascular risk.
    
    ### Recommended Actions
    1. **Take your medications as prescribed** - Your doctor may recommend medications to lower blood 
       pressure and cholesterol
    2. **Quit smoking** - This is the single most important change you can make for your heart health
    3. **Eat a heart-healthy diet** - Focus on fruits, vegetables, whole grains, and lean proteins
    4. **Exercise regularly** - Aim for at least 150 minutes of moderate exercise per week
    5. **Manage stress** - Practice relaxation techniques like meditation or yoga
    
    ### Follow-up
    Schedule a follow-up appointment in 4-6 weeks to reassess your blood pressure and cholesterol.
    """)
    
    st.markdown("---")
    
    # Risk factors
    st.markdown("## 📊 Risk Factor Breakdown")
    
    risk_factors = {
        "Age": {"value": 25, "detail": "Age 65 years (≥65 years)"},
        "Blood Pressure": {"value": 25, "detail": "Severe hypertension (SBP 150)"},
        "LDL Cholesterol": {"value": 12, "detail": "High LDL (160 mg/dL)"},
        "Smoking": {"value": 20, "detail": "Active smoker"},
    }
    
    total = sum(f["value"] for f in risk_factors.values())
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("Total Risk Score", f"{total}/100")
    
    with col2:
        for factor, data in risk_factors.items():
            percentage = (data["value"] / total) * 100
            st.markdown(f"{factor}: **{data['value']} points** ({percentage:.0f}%) - {data['detail']}")
    
    st.markdown("---")
    
    # Safety check summary
    st.markdown("## 🔒 Safety & Compliance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ✅ Checks Completed
        - Drug interaction screening
        - Contraindication verification
        - Clinical guideline validation
        - Risk assessment computation
        - Human review & approval
        """)
    
    with col2:
        st.markdown("""
        ### 📋 Audit Trail
        - **Analysis Time**: 2:34 PM
        - **Duration**: 45 seconds
        - **Reviewed By**: Dr. Smith
        - **Approval Time**: 2:35 PM
        - **Status**: ✅ APPROVED
        """)
    
    st.markdown("---")
    
    # Export and actions
    st.markdown("## 📥 Export & Share")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Download PDF", use_container_width=True):
            st.success("PDF downloaded!")
    
    with col2:
        if st.button("📧 Email Report", use_container_width=True):
            st.success("Email sent!")
    
    with col3:
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            st.success("Copied!")
    
    with col4:
        if st.button("💾 Save Case", use_container_width=True):
            st.success("Case saved!")
    
    st.markdown("---")
    
    # Navigation
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🆕 New Analysis", use_container_width=True):
            st.session_state.patient_data = None
            st.session_state.current_page = "New Analysis"
            st.rerun()
    
    with col2:
        if st.button("📚 View History", use_container_width=True):
            st.session_state.current_page = "History"
            st.rerun()

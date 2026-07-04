"""New analysis page - patient input and workflow initiation."""

import streamlit as st
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def render():
    """Render new analysis page."""
    
    st.markdown("## 🆕 New Clinical Analysis")
    
    # Info box
    st.info("""
    Enter patient information and clinical query to start the multi-agent analysis.
    The system will retrieve guidelines, assess risk, check medication safety, and generate 
    patient-friendly recommendations.
    """)
    
    # Create form
    with st.form("patient_analysis_form", border=True):
        st.markdown("### 👤 Patient Demographics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            age = st.number_input(
                "Age (years)",
                min_value=18,
                max_value=120,
                value=65,
                help="Patient age in years"
            )
        
        with col2:
            sex = st.selectbox(
                "Sex",
                ["Male", "Female", "Other"],
                help="Patient biological sex"
            )
        
        with col3:
            bmI = st.number_input(
                "BMI (kg/m²)",
                min_value=10.0,
                max_value=60.0,
                value=28.0,
                step=0.1,
                help="Body Mass Index"
            )
        
        st.markdown("### 💉 Cardiovascular Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bp_sys = st.number_input(
                "Systolic BP (mmHg)",
                min_value=70,
                max_value=250,
                value=150,
                help="Systolic blood pressure"
            )
        
        with col2:
            bp_dia = st.number_input(
                "Diastolic BP (mmHg)",
                min_value=40,
                max_value=150,
                value=95,
                help="Diastolic blood pressure"
            )
        
        with col3:
            heart_rate = st.number_input(
                "Heart Rate (bpm)",
                min_value=40,
                max_value=200,
                value=72,
                help="Resting heart rate"
            )
        
        st.markdown("### 🧪 Laboratory Values")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ldl = st.number_input(
                "LDL Cholesterol (mg/dL)",
                min_value=0,
                max_value=400,
                value=160,
                help="Low-density lipoprotein cholesterol"
            )
        
        with col2:
            hdl = st.number_input(
                "HDL Cholesterol (mg/dL)",
                min_value=0,
                max_value=200,
                value=45,
                help="High-density lipoprotein cholesterol"
            )
        
        with col3:
            triglycerides = st.number_input(
                "Triglycerides (mg/dL)",
                min_value=0,
                max_value=600,
                value=150,
                help="Serum triglycerides"
            )
        
        st.markdown("### 📋 Medical Conditions")
        
        conditions = st.multiselect(
            "Active Conditions",
            [
                "Hypertension",
                "Dyslipidemia",
                "Diabetes",
                "Chronic Kidney Disease",
                "Smoking",
                "Atrial Fibrillation",
                "Obesity",
                "Metabolic Syndrome",
                "Family History of ASCVD",
            ],
            default=["Hypertension", "Smoking"],
            help="Select all applicable conditions"
        )
        
        st.markdown("### 💊 Current Medications")
        
        medications = st.multiselect(
            "Current Medications",
            [
                "ACE Inhibitor",
                "ARB",
                "Beta-Blocker",
                "Thiazide Diuretic",
                "Statin",
                "Aspirin",
                "Warfarin",
                "DOAC",
                "Metformin",
                "Sulfonylurea",
            ],
            default=[],
            help="Select all current medications"
        )
        
        st.markdown("### ❓ Clinical Query")
        
        query = st.text_area(
            "Clinical Question",
            value="What is the first-line therapy for this patient?",
            height=100,
            help="Enter the clinical question or indication for analysis",
            placeholder="E.g., 'What is first-line therapy?', 'Is this patient a candidate for...', etc."
        )
        
        st.markdown("### 📝 Additional Notes")
        
        notes = st.text_area(
            "Clinical Notes (Optional)",
            height=80,
            placeholder="Any additional clinical context or considerations...",
            help="Optional clinical notes for context"
        )
        
        st.markdown("---")
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            submitted = st.form_submit_button(
                "🚀 Start Analysis",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Prepare data
            patient_data = {
                "age": age,
                "sex": sex,
                "bmi": bmI,
                "bp": f"{bp_sys}/{bp_dia}",
                "heart_rate": heart_rate,
                "ldl": ldl,
                "hdl": hdl,
                "triglycerides": triglycerides,
                "conditions": conditions,
                "medications": medications,
                "notes": notes,
            }
            
            # Store in session
            st.session_state.patient_data = patient_data
            st.session_state.clinical_query = query
            st.session_state.workflow_started_at = datetime.now()
            
            logger.info(f"Started analysis for {age}yo patient")
            
            # Show success and switch to workflow page
            st.success("✅ Analysis started! Switching to workflow view...")
            st.session_state.current_page = "Active Workflow"
            st.rerun()

"""Case history and past analyses."""

import streamlit as st
from datetime import datetime, timedelta


def render():
    """Render history page."""
    
    st.markdown("## 📚 Case History")
    
    st.info("View your previous analyses and cases.")
    
    # Mock history data
    cases = [
        {
            "id": "CASE001",
            "date": datetime.now() - timedelta(hours=2),
            "patient": "65M",
            "risk": "High",
            "status": "Completed",
            "query": "First-line therapy?",
        },
        {
            "id": "CASE002",
            "date": datetime.now() - timedelta(days=1),
            "patient": "58F",
            "risk": "Moderate",
            "status": "Completed",
            "query": "Safety check for medication",
        },
        {
            "id": "CASE003",
            "date": datetime.now() - timedelta(days=3),
            "patient": "72M",
            "risk": "Very High",
            "status": "Approved",
            "query": "Comprehensive assessment",
        },
    ]
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_filter = st.multiselect(
            "Risk Level",
            ["Low", "Moderate", "High", "Very High"],
            default=["Low", "Moderate", "High", "Very High"]
        )
    
    with col2:
        status_filter = st.multiselect(
            "Status",
            ["Completed", "Approved", "Rejected", "Pending"],
            default=["Completed", "Approved"]
        )
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Most Recent", "Patient Age", "Risk Level"])
    
    st.markdown("---")
    
    # Display cases
    if not cases:
        st.info("No cases found.")
    else:
        for case in cases:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 2, 1])
            
            with col1:
                st.markdown(f"**{case['id']}**")
            
            with col2:
                st.markdown(f"{case['date'].strftime('%m/%d %H:%M')}")
            
            with col3:
                if case['risk'] == 'Very High':
                    st.markdown("🔴 Very High")
                elif case['risk'] == 'High':
                    st.markdown("🟠 High")
                elif case['risk'] == 'Moderate':
                    st.markdown("🟡 Moderate")
                else:
                    st.markdown("🟢 Low")
            
            with col4:
                st.markdown(case['query'])
            
            with col5:
                if st.button("👁️ View", key=f"view_{case['id']}", use_container_width=True):
                    st.info(f"Loading case {case['id']}...")
    
    st.markdown("---")
    
    # Statistics
    st.markdown("## 📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cases", len(cases))
    
    with col2:
        st.metric("This Month", "3")
    
    with col3:
        st.metric("Completion Rate", "100%")
    
    with col4:
        st.metric("Avg Duration", "45s")

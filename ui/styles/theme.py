"""CardioSentinel UI Theme and Styling."""

import streamlit as st
from pathlib import Path
from config import COLORS


def load_external_css(css_path: str = "ui/styles/style.css") -> None:
    """Load and inject CSS from an external file."""
    path = Path(css_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ CSS file not found: {css_path}")


def apply_theme(theme_name: str = "dark"):
    """Apply theme configuration."""
    if theme_name.lower() == "dark":
        apply_dark_theme()
    elif theme_name.lower() == "light":
        apply_light_theme()
    else:
        apply_auto_theme()


def apply_dark_theme():
    """Apply dark theme."""
    st.markdown("""
    <style>
    :root {
        --primary-color: #E63946;
        --secondary-color: #457B9D;
        --success-color: #2A9D8F;
        --warning-color: #F4A261;
        --danger-color: #E63946;
        --light-color: #F1FAEE;
        --dark-color: #1A1A1A;
        --bg-gradient-start: #0f0c29;
        --bg-gradient-end: #302b63;
    }
    </style>
    """, unsafe_allow_html=True)


def apply_light_theme():
    """Apply light theme."""
    st.markdown("""
    <style>
    :root {
        --primary-color: #E63946;
        --secondary-color: #457B9D;
        --success-color: #2A9D8F;
        --warning-color: #F4A261;
        --danger-color: #E63946;
        --light-color: #FFFFFF;
        --dark-color: #333333;
        --bg-gradient-start: #f8f9fa;
        --bg-gradient-end: #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)


def apply_auto_theme():
    """Apply automatic theme based on system preference."""
    st.markdown("""
    <style>
    @media (prefers-color-scheme: dark) {
        :root {
            --primary-color: #E63946;
            --secondary-color: #457B9D;
            --bg-gradient-start: #0f0c29;
            --bg-gradient-end: #302b63;
        }
    }
    @media (prefers-color-scheme: light) {
        :root {
            --primary-color: #E63946;
            --secondary-color: #457B9D;
            --bg-gradient-start: #f8f9fa;
            --bg-gradient-end: #e9ecef;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def apply_custom_css():
    """Apply custom cardiovascular-themed CSS."""
    st.markdown("""
    <style>
    /* Cardiovascular Color Palette */
    :root {
        --primary: #E63946;
        --secondary: #457B9D;
        --success: #2A9D8F;
        --warning: #F4A261;
        --danger: #E63946;
        --light: #F1FAEE;
        --dark: #1A1A1A;
        --ecg: #00D084;
    }
    
    /* ECG Wave Animation */
    @keyframes ecg-pulse {
        0%, 100% { transform: translateX(-100%); }
        50% { transform: translateX(0%); }
    }
    
    @keyframes heartbeat {
        0%, 100% { transform: scale(1); }
        25% { transform: scale(1.05); }
        50% { transform: scale(1); }
    }
    
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(230, 57, 70, 0.7); }
        50% { box-shadow: 0 0 0 10px rgba(230, 57, 70, 0); }
    }
    
    /* Global Styling */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary);
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        padding: 0.5rem 1.5rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(230, 57, 70, 0.3);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary) 0%, #C1121F 100%);
        color: white;
    }
    
    /* Cards and Containers */
    .stMetric {
        background: rgba(69, 123, 157, 0.1);
        border-left: 4px solid var(--secondary);
        padding: 1rem;
        border-radius: 6px;
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        background: rgba(69, 123, 157, 0.15);
        transform: translateX(4px);
    }
    
    .stExpander {
        border: 1px solid rgba(230, 57, 70, 0.2) !important;
        border-radius: 6px !important;
    }
    
    .stExpander > div > div > button {
        color: var(--primary) !important;
        font-weight: 600 !important;
    }
    
    /* Success, Info, Warning, Error boxes */
    .stSuccess {
        background: rgba(42, 157, 143, 0.1) !important;
        border-left: 4px solid var(--success) !important;
        border-radius: 6px !important;
    }
    
    .stInfo {
        background: rgba(69, 123, 157, 0.1) !important;
        border-left: 4px solid var(--secondary) !important;
        border-radius: 6px !important;
    }
    
    .stWarning {
        background: rgba(244, 162, 97, 0.1) !important;
        border-left: 4px solid var(--warning) !important;
        border-radius: 6px !important;
    }
    
    .stError {
        background: rgba(230, 57, 70, 0.1) !important;
        border-left: 4px solid var(--danger) !important;
        border-radius: 6px !important;
    }
    
    /* Form inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 2px solid rgba(230, 57, 70, 0.2) !important;
        border-radius: 6px !important;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(230, 57, 70, 0.1) !important;
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
        border-radius: 3px;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, rgba(69, 123, 157, 0.1) 0%, rgba(230, 57, 70, 0.05) 100%);
    }
    
    /* Tabs */
    .stTabs [role="tablist"] {
        border-bottom: 2px solid rgba(230, 57, 70, 0.2);
    }
    
    .stTabs [role="tab"] {
        color: #999;
        border-bottom: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .stTabs [role="tab"][aria-selected="true"] {
        color: var(--primary);
        border-bottom: 2px solid var(--primary);
    }
    
    /* ECG Background Animation */
    .ecg-background {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.03;
        pointer-events: none;
        z-index: -1;
    }
    
    /* Heart pulse animation */
    .heart-pulse {
        display: inline-block;
        animation: heartbeat 1.5s infinite;
    }
    
    /* Risk badges */
    .risk-very-high {
        background: rgba(230, 57, 70, 0.2);
        border-left: 4px solid #E63946;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        color: #E63946;
        font-weight: 600;
    }
    
    .risk-high {
        background: rgba(244, 162, 97, 0.2);
        border-left: 4px solid #F4A261;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        color: #F4A261;
        font-weight: 600;
    }
    
    .risk-moderate {
        background: rgba(255, 193, 7, 0.2);
        border-left: 4px solid #FFC107;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        color: #FFC107;
        font-weight: 600;
    }
    
    .risk-low {
        background: rgba(42, 157, 143, 0.2);
        border-left: 4px solid #2A9D8F;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        color: #2A9D8F;
        font-weight: 600;
    }
    
    /* Smooth transitions */
    * {
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)


def render_ecg_background():
    """Render animated ECG background."""
    st.markdown("""
    <svg class="ecg-background" viewBox="0 0 1000 100" preserveAspectRatio="none">
        <defs>
            <linearGradient id="ecg-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:rgb(0,208,132);stop-opacity:0.1" />
                <stop offset="50%" style="stop-color:rgb(230,57,70);stop-opacity:0.05" />
                <stop offset="100%" style="stop-color:rgb(69,123,157);stop-opacity:0.1" />
            </linearGradient>
        </defs>
        <polyline points="0,50 10,50 20,40 30,60 40,50 50,50 60,30 70,70 80,50 90,50 100,45 110,55 120,50 130,50 140,35 150,65 160,50 170,50 180,40 190,60 200,50 210,50 220,30 230,70 240,50 250,50 260,45 270,55 280,50 290,50 300,35 310,65 320,50 330,50 340,40 350,60 360,50 370,50 380,30 390,70 400,50 410,50 420,45 430,55 440,50 450,50 460,35 470,65 480,50 490,50 500,40 510,60 520,50 530,50 540,30 550,70 560,50 570,50 580,45 590,55 600,50 610,50 620,35 630,65 640,50 650,50 660,40 670,60 680,50 690,50 700,30 710,70 720,50 730,50 740,45 750,55 760,50 770,50 780,35 790,65 800,50 810,50 820,40 830,60 840,50 850,50 860,30 870,70 880,50 890,50 900,45 910,55 920,50 930,50 940,35 950,65 960,50 970,50 980,40 990,60 1000,50" 
            fill="none" stroke="url(#ecg-gradient)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """, unsafe_allow_html=True)
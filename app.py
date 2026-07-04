"""CardioSentinel MAS - Streamlit UI Entry Point."""

import streamlit as st
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CardioSentinel | Clinical Decision Support",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "https://github.com/anaboset/cardiosentinel",
        "Report a bug": "https://github.com/anaboset/cardiosentinel/issues",
        "About": "CardioSentinel MAS v1.0 — Multi-Agent Clinical Reasoning System",
    }
)

# ─── IMPORTS ─────────────────────────────────────────────────────────────────
from pages import history, home, new_analysis, results, review, workflow
from ui.styles.theme import apply_theme, apply_custom_css, load_external_css

# ─── LOAD ALL STYLES ─────────────────────────────────────────────────────────
# 1. External CSS: layout, navigation, structural styles
load_external_css("ui/styles/style.css")

# 2. Theme CSS: colors, variables, component theming
apply_theme(st.session_state.get("theme", "dark"))

# 3. Custom CSS: cardiovascular-specific styling (buttons, inputs, badges, ECG)
apply_custom_css()

# ─── SESSION STATE INITIALIZATION ────────────────────────────────────────────
defaults = {
    "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
    "theme": "dark",
    "current_page": "Home",
    "current_workflow": None,
    "analytics_enabled": True,
    "autosave_enabled": True,
    "notification_count": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
        if key == "session_id":
            logger.info(f"New session: {value}")

# ─── NAVIGATION CONFIGURATION ────────────────────────────────────────────────
NAV_PAGES = {
    "Home": {"icon": "🏠", "module": home, "badge": None},
    "New Analysis": {"icon": "🔬", "module": new_analysis, "badge": None},
    "Active Workflow": {"icon": "⚡", "module": workflow, "badge": "live"},
    "Review & Approve": {"icon": "✅", "module": review, "badge": None},
    "Results": {"icon": "📊", "module": results, "badge": None},
    "History": {"icon": "📜", "module": history, "badge": None},
}

# ─── TOP NAVIGATION BAR ──────────────────────────────────────────────────────
def render_nav_bar():
    """Render the top bar (brand + status) and the real page-nav buttons."""
    workflow_status = st.session_state.current_workflow.get("status", "Idle") if st.session_state.current_workflow else "Idle"
    status_color = "#2ecc71" if workflow_status == "Active" else "#95a5a6"

    # Brand bar — no fake nav items anymore, just branding + status
    st.markdown(f"""
    <div class="top-nav-container">
        <div class="nav-brand">
            <span class="nav-brand-icon">🫀</span>
            <span>CardioSentinel</span>
            <span style="font-size: 0.7rem; opacity: 0.7; font-weight: 400; margin-left: 8px;">MAS</span>
        </div>
        <div class="nav-actions">
            <div class="status-pill">
                <span class="status-dot" style="background: {status_color};"></span>
                <span>{workflow_status}</span>
            </div>
            <button class="nav-btn" onclick="window.location.reload()">🔄</button>
            <button class="nav-btn" title="Settings">⚙️</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Real nav — wrapped in a keyed container so CSS can target just this row
    with st.container(key="nav_row"):
        cols = st.columns(len(NAV_PAGES))
        for idx, (page_name, config) in enumerate(NAV_PAGES.items()):
            with cols[idx]:
                btn_label = f"{config['icon']} {page_name}"
                if config["badge"] == "live":
                    btn_label += " ●"

                if st.button(
                    btn_label,
                    key=f"nav_{page_name}",
                    type="primary" if st.session_state.current_page == page_name else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.current_page = page_name
                    st.rerun()

# ─── SETTINGS PANEL ──────────────────────────────────────────────────────────
def render_settings_panel():
    """Render application settings inside the sidebar."""
    with st.sidebar:
        st.markdown("### ⚙️ Application Settings")

        st.markdown("**🎨 Appearance**")
        theme = st.segmented_control(
            "Theme",
            options=["Light", "Dark", "Auto"],
            default=st.session_state.theme.capitalize(),
            key="theme_selector"
        )
        if theme and theme.lower() != st.session_state.theme:
            st.session_state.theme = theme.lower()
            st.rerun()

        st.markdown("**🔧 Preferences**")
        st.session_state.analytics_enabled = st.toggle(
            "Enable Analytics",
            value=st.session_state.analytics_enabled,
            help="Collect usage metrics for system improvement"
        )
        st.session_state.autosave_enabled = st.toggle(
            "Auto-save Decisions",
            value=st.session_state.autosave_enabled,
            help="Automatically save clinical decisions"
        )

        st.markdown("---")
        st.markdown("**ℹ️ Session Info**")
        st.caption(f"**Session ID:** `{st.session_state.session_id}`")
        st.caption(f"**Started:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.caption(f"**Version:** v1.0 Phase II")


# ─── MAIN RENDER ──────────────────────────────────────────────────────────────
def main():
    render_nav_bar()
    render_settings_panel()  # renders into the sidebar now

    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    current = st.session_state.current_page
    
    try:
        if current == "Home":
            home.render()
        elif current == "New Analysis":
            new_analysis.render()
        elif current == "Active Workflow":
            workflow.render()
        elif current == "Review & Approve":
            review.render()
        elif current == "Results":
            results.render()
        elif current == "History":
            history.render()
        else:
            st.error(f"Unknown page: {current}")
            st.session_state.current_page = "Home"
            st.rerun()
    except Exception as e:
        st.error(f"Error loading page '{current}': {str(e)}")
        logger.error(f"Page render error: {e}", exc_info=True)
        if st.button("🏠 Return to Home"):
            st.session_state.current_page = "Home"
            st.rerun()
    
    st.markdown("""
    <div class="app-footer">
        <div class="footer-warning">
            <span>⚠️</span>
            <span><strong>For research and demonstration purposes only.</strong> Not for clinical use.</span>
        </div>
        <p>CardioSentinel MAS v1.0 | Phase II: Multi-Agent Clinical Reasoning</p>
        <p style="opacity: 0.6; margin-top: 0.5rem;">
            Multi-Agent AI System for Cardiovascular Care
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
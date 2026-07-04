"""Component library for CardioSentinel UI."""

import streamlit as st
from typing import Dict, Any, List


def render_risk_badge(risk_level: str, score: float = None) -> None:
    """Render a risk classification badge."""
    
    risk_colors = {
        "low": ("#2A9D8F", "🟢"),
        "moderate": ("#F4A261", "🟡"),
        "high": ("#F4A261", "🟠"),
        "very_high": ("#E63946", "🔴"),
    }
    
    color, emoji = risk_colors.get(risk_level.lower(), ("#999", "⚪"))
    
    label = risk_level.replace("_", " ").title()
    if score is not None:
        label += f" ({score}/100)"
    
    st.markdown(f"""
    <div style="display: inline-block; background-color: {color}20; border-left: 4px solid {color}; 
    padding: 0.5rem 1rem; border-radius: 4px; color: {color}; font-weight: 600;">
        {emoji} {label}
    </div>
    """, unsafe_allow_html=True)


def render_agent_card(agent_name: str, status: str, output: str = None, duration: float = None) -> None:
    """Render an agent execution card."""
    
    status_colors = {
        "pending": "#999",
        "running": "#F4A261",
        "completed": "#2A9D8F",
        "failed": "#E63946",
    }
    
    status_emojis = {
        "pending": "⊙",
        "running": "⟳",
        "completed": "✅",
        "failed": "❌",
    }
    
    color = status_colors.get(status, "#999")
    emoji = status_emojis.get(status, "?")
    
    duration_str = f" ({duration:.2f}s)" if duration else ""
    
    st.markdown(f"""
    <div style="background-color: {color}10; border-left: 4px solid {color}; padding: 1rem; 
    border-radius: 6px; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5em; margin-right: 0.5rem;">{emoji}</span>
            <span style="font-weight: 600; color: {color}; font-size: 1.1em;">
                {agent_name}{duration_str}
            </span>
            <span style="margin-left: auto; color: {color}; font-weight: 600;">
                {status.upper()}
            </span>
        </div>
        {f'<div style="color: #999; font-size: 0.9em; margin-top: 0.5rem;">{output}</div>' if output else ''}
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(title: str, value: str, unit: str = "", icon: str = "") -> None:
    """Render a metric display card."""
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(69, 123, 157, 0.1) 0%, rgba(230, 57, 70, 0.05) 100%);
    border-radius: 8px; padding: 1.5rem; border: 1px solid rgba(230, 57, 70, 0.2); margin: 0.5rem 0;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="color: #999; font-size: 0.9em; margin-bottom: 0.5rem;">{title}</div>
                <div style="font-size: 2em; font-weight: 700; color: #E63946;">
                    {value} <span style="font-size: 0.6em; color: #666;">{unit}</span>
                </div>
            </div>
            <div style="font-size: 2.5em; opacity: 0.3;">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_approval_section(checkpoint_data: Dict[str, Any]) -> Dict[str, Any]:
    """Render an approval checkpoint section."""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### {checkpoint_data['title']}")
        st.markdown(checkpoint_data['description'])
    
    with col2:
        decision = st.radio(
            "Decision",
            ["Approve", "Modify", "Reject"],
            key=f"decision_{checkpoint_data['id']}",
            horizontal=True,
            label_visibility="collapsed"
        )
    
    if decision == "Modify":
        modifications = st.text_area(
            "Modification details",
            key=f"mods_{checkpoint_data['id']}",
            label_visibility="collapsed"
        )
        return {"decision": "modify", "modifications": modifications}
    
    return {"decision": decision.lower()}


def render_workflow_timeline(events: List[Dict[str, Any]]) -> None:
    """Render a timeline of workflow events."""
    
    timeline_html = '<div style="position: relative; padding: 2rem 0;">'
    timeline_html += '<div style="position: absolute; left: 20px; top: 0; bottom: 0; width: 2px; background: linear-gradient(180deg, #E63946 0%, #457B9D 100%);"></div>'
    
    for i, event in enumerate(events):
        status_color = "#2A9D8F" if event['status'] == 'completed' else "#F4A261"
        
        timeline_html += f'''
        <div style="margin-left: 60px; margin-bottom: 2rem; position: relative;">
            <div style="position: absolute; left: -40px; top: 8px; width: 16px; height: 16px; background: {status_color}; 
            border: 3px solid white; border-radius: 50%; box-shadow: 0 0 0 3px {status_color}20;"></div>
            <div style="font-weight: 600; color: #E63946; margin-bottom: 0.5rem;">{event['title']}</div>
            <div style="color: #999; font-size: 0.9em; margin-bottom: 0.25rem;">{event['time']}</div>
            {f"<div style='color: #666;'>{event['description']}</div>" if 'description' in event else ''}
        </div>
        '''
    
    timeline_html += '</div>'
    st.markdown(timeline_html, unsafe_allow_html=True)

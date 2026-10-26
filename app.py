"""InternFlow AI — Intern Task Allocation & Review Management System.

Main Application Controller and Streamlit Navigation Hub.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from database.connection import init_db
from database.seed_data import seed_database_if_empty
from config.settings import APP_NAME, DEMO_MODE
from ui.styles import apply_custom_styles
from ui.auth import init_auth_session, render_user_profile_sidebar
from ui.dashboard_view import render_dashboard_view
from ui.interns_view import render_interns_view
from ui.excel_view import render_excel_view
from ui.task_allocation_view import render_task_allocation_view
from ui.task_explanation_view import render_task_explanation_view
from ui.submissions_view import render_submissions_view
from ui.verification_view import render_verification_view
from ui.mentor_workspace_view import render_mentor_workspace_view
from ui.calendar_view import render_calendar_view
from ui.email_center_view import render_email_center_view
from ui.analytics_view import render_analytics_view
from ui.settings_view import render_settings_view
from ui.audit_view import render_audit_view

# Streamlit Page Configuration
st.set_page_config(
    page_title=f"{APP_NAME} — Enterprise Intern Management",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Custom Styling
apply_custom_styles()

# Initialize Database tables if needed
init_auth_session()
try:
    init_db()
except Exception as e:
    st.error(f"Database initialization note: {e}")


def main():
    # Render Profile in Sidebar
    render_user_profile_sidebar()

    # Sidebar Navigation Menu (Admin Console)
    st.sidebar.markdown("### 🧭 Admin Navigation")

    nav_options = [
        "🏠 Main Dashboard",
        "📊 Excel Import & Export",
        "👥 Intern Management",
        "📋 Task Allocation",
        "💡 AI Task Explanations (Voice & Text)",
        "📤 Submission Portal",
        "🤖 AI Verification Reports (Good vs Not Good)",
        "✍️ Review Management Workspace",
        "📅 Review Calendar (Google Meet)",
        "✉️ Email Automation Center",
        "📈 Analytics & Reports",
        "⚙️ Settings & Integrations",
        "🛡️ Audit Logs",
    ]

    page_choice = st.sidebar.radio("Go to:", nav_options, index=0)

    # Top Capsule Navigation Bar (faithfully matching reference image)
    st.markdown(
        f"""
        <div class="binke-nav-bar">
            <div class="binke-logo">
                <span style="background: #9B72CF; color: white; width: 32px; height: 32px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 16px; border: 2px solid #1E1E24;">✦</span>
                <span>InternFlow</span>
            </div>
            <div class="binke-nav-links">
                <span class="binke-pill pill-purple">Dashboard</span>
                <span class="binke-pill pill-lime">Voice AI</span>
                <span class="binke-pill" style="border: 2px solid #1E1E24; background: white; color: #1E1E24;">Google Meet</span>
                <span class="binke-pill" style="border: 2px solid #1E1E24; background: white; color: #1E1E24;">22+ Languages</span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span class="binke-pill pill-lime" style="font-size: 11px;">
                    ✨ GEMINI 3.5 ACTIVE
                </span>
                <span class="pill-black" style="font-size: 12px; cursor: pointer;">
                    🛡️ ADMIN: {st.session_state.full_name}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Routing to Pages
    if "Main Dashboard" in page_choice:
        render_dashboard_view()
    elif "Intern Management" in page_choice:
        render_interns_view()
    elif "Excel Import & Export" in page_choice:
        render_excel_view()
    elif "Task Allocation" in page_choice:
        render_task_allocation_view()
    elif "AI Task Explanations" in page_choice:
        render_task_explanation_view()
    elif "Submission Portal" in page_choice:
        render_submissions_view()
    elif "AI Verification Reports" in page_choice:
        render_verification_view()
    elif "Review Management Workspace" in page_choice or "Mentor Review" in page_choice:
        render_mentor_workspace_view()
    elif "Review Calendar" in page_choice:
        render_calendar_view()
    elif "Email Automation Center" in page_choice:
        render_email_center_view()
    elif "Analytics & Reports" in page_choice:
        render_analytics_view()
    elif "Settings & Integrations" in page_choice:
        render_settings_view()
    elif "Audit Logs" in page_choice:
        render_audit_view()


if __name__ == "__main__":
    main()

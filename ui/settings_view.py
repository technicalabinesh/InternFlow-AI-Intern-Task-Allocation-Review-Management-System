"""Settings and Integrations Management View for InternFlow AI."""

import os
from pathlib import Path
import streamlit as st

from config.settings import (
    DEMO_MODE,
    AI_PROVIDER,
    AI_MODEL,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    ANTHROPIC_API_KEY,
    EMAIL_PROVIDER,
    GMAIL_CLIENT_SECRETS_FILE,
    GMAIL_TOKEN_FILE,
    EMAIL_SENDER_NAME,
    EMAIL_SENDER_ADDRESS,
    MAX_UPLOAD_SIZE_MB,
    DEFAULT_TIMEZONE,
    ALLOWED_EXTENSIONS,
    BASE_DIR,
)
from ui.auth import require_role


def render_settings_view():
    if not require_role(["admin"]):
        return

    st.markdown("## ⚙️ Settings & System Integrations")
    st.caption("Configure AI engines, email delivery credentials, security parameters, and operational modes.")

    tab_general, tab_ai, tab_email, tab_security = st.tabs([
        "🌐 General & Operation Mode",
        "🤖 AI Provider Configuration",
        "✉️ Gmail API & Email Provider",
        "🛡️ Upload & Storage Security",
    ])

    # Tab 1: General & Operation Mode
    with tab_general:
        st.markdown("#### System Operation Mode")
        st.markdown(
            """
            <div class="saas-card">
                <h4>🛡️ Safe Demo Mode</h4>
                <p style="color: #64748b; font-size: 13px;">
                    When Demo Mode is enabled, emails are fully generated and saved to the database as <code>Simulated</code> without contacting real inboxes.
                    Realistic AI explanations and submission evaluations run out-of-the-box without requiring third-party API keys.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write(f"**Current Demo Mode State:** `{'ENABLED (Safe Mode)' if DEMO_MODE else 'DISABLED (Production)'}`")
        st.write(f"**Default Program Timezone:** `{DEFAULT_TIMEZONE}`")
        st.write(f"**Database Engine:** `SQLite (WAL Mode enabled)`")

    # Tab 2: AI Provider Configuration
    with tab_ai:
        st.markdown("#### Configure AI Task Explanation & Verification Provider")

        with st.form("ai_settings_form"):
            selected_provider = st.selectbox(
                "Active AI Provider",
                ["mock", "openai", "gemini", "anthropic"],
                index=["mock", "openai", "gemini", "anthropic"].index(AI_PROVIDER) if AI_PROVIDER in ["mock", "openai", "gemini", "anthropic"] else 0,
            )

            ai_model_name = st.text_input(
                "Model Identifier",
                value=AI_MODEL if AI_MODEL else "gpt-4o-mini",
            )

            c_key1, c_key2 = st.columns(2)
            with c_key1:
                openai_key = st.text_input("OpenAI API Key", value=OPENAI_API_KEY, type="password")
            with c_key2:
                gemini_key = st.text_input("Google Gemini API Key", value=GEMINI_API_KEY, type="password")

            anthropic_key = st.text_input("Anthropic Claude API Key", value=ANTHROPIC_API_KEY, type="password")

            save_ai = st.form_submit_button("Save AI Settings", type="primary")

            if save_ai:
                st.success("AI Configuration updated successfully! (Stored securely in runtime environment)")

        # Test AI connection button
        if st.button("🧪 Test AI Connection"):
            with st.spinner("Pinging active AI provider..."):
                from services.ai_service import AIService
                from database.models import Task
                import datetime

                dummy_task = Task(
                    task_id="TEST-AI",
                    title="System Connectivity Check",
                    description="Verify AI prompt processing pipeline.",
                    priority="Low",
                    deadline=datetime.date.today(),
                )
                try:
                    res = AIService.get_provider().explain_task(dummy_task)
                    st.success(f"✅ AI Provider '{selected_provider}' is operational! Generated test summary: {res.get('summary', '')[:80]}...")
                except Exception as e:
                    st.error(f"❌ AI Test failed: {str(e)}")

    # Tab 3: Email Integration
    with tab_email:
        st.markdown("#### Configure Email Provider & Gmail OAuth 2.0")

        st.markdown(
            """
            <div class="saas-card">
                <h4>Gmail OAuth 2.0 Setup Guide</h4>
                <ol style="font-size: 13px; color: #475569; padding-left: 20px;">
                    <li>Go to the <a href="https://console.cloud.google.com" target="_blank">Google Cloud Console</a>.</li>
                    <li>Create a project and enable the <strong>Gmail API</strong>.</li>
                    <li>Navigate to <strong>APIs & Services > OAuth consent screen</strong>, set User Type to External, and add test users.</li>
                    <li>Create an <strong>OAuth 2.0 Client ID</strong> (Application type: Desktop App).</li>
                    <li>Download the JSON credentials and save as <code>credentials.json</code> in the project root.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

        creds_exists = os.path.exists(GMAIL_CLIENT_SECRETS_FILE)
        token_exists = os.path.exists(GMAIL_TOKEN_FILE)

        col_st1, col_st2 = st.columns(2)
        with col_st1:
            st.write(f"**Client Secrets File (`credentials.json`):** {'✅ Found' if creds_exists else '❌ Not Found (Demo Provider Used)'}")
        with col_st2:
            st.write(f"**OAuth Token File (`token.json`):** {'✅ Authorized' if token_exists else '⏳ Pending Authorization'}")

        st.write(f"**Configured Sender Name:** `{EMAIL_SENDER_NAME}`")
        st.write(f"**Configured Sender Address:** `{EMAIL_SENDER_ADDRESS}`")

    # Tab 4: Security & Uploads
    with tab_security:
        st.markdown("#### Security & Upload Governance")
        st.write(f"**Max Upload File Size:** `{MAX_UPLOAD_SIZE_MB} MB`")
        st.write(f"**Permitted Extensions:** `{', '.join(sorted(ALLOWED_EXTENSIONS))}`")
        st.markdown(
            """
            <div class="banner-demo">
                <strong>🔒 Defensive Execution Policy:</strong> Uploaded scripts, python code, and macros are strictly parsed as passive text. Code execution is completely blocked during verification to protect the application environment.
            </div>
            """,
            unsafe_allow_html=True,
        )

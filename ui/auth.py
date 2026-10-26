"""Authentication and Admin Role handling in Streamlit."""

import hashlib
import streamlit as st


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_auth_session():
    """Ensure session state variables for Admin coordinator are initialized."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = True
        st.session_state.username = "admin"
        st.session_state.full_name = "Admin Coordinator"
        st.session_state.email = "m.abinesh555@gmail.com"
        st.session_state.role = "admin"
        st.session_state.department = "Internship Operations"


def render_user_profile_sidebar():
    """Render Admin console badge and coordinator profile in the sidebar."""
    init_auth_session()

    st.sidebar.markdown(
        f"""
        <div style="background: #ffffff; border: 2.5px solid #1E1E24; border-radius: 16px; padding: 14px; margin-bottom: 14px; box-shadow: 4px 4px 0px #1E1E24;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 11px; font-weight: 800; color: #64748B; letter-spacing: 0.05em; text-transform: uppercase;">ADMIN CONSOLE</span>
                <span class="badge badge-approved" style="font-size: 10px; padding: 2px 8px;">ACTIVE</span>
            </div>
            <div style="font-size: 16px; font-weight: 800; color: #1E1E24;">{st.session_state.full_name}</div>
            <div style="font-size: 12px; color: #64748B; word-break: break-all; margin-top: 2px;">{st.session_state.email}</div>
            <div style="margin-top: 10px;">
                <span style="background: #D4F074; color: #1E1E24; border: 1.5px solid #1E1E24; font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 99px; box-shadow: 2px 2px 0px #1E1E24;">
                    🛡️ SUPER ADMIN
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick profile edit for the admin
    with st.sidebar.expander("⚙️ Coordinator Profile Settings", expanded=False):
        new_name = st.text_input("Coordinator Name", value=st.session_state.full_name, key="edit_coord_name")
        new_email = st.text_input("Notification Email", value=st.session_state.email, key="edit_coord_email")
        if st.button("Save Profile", use_container_width=True, type="primary"):
            st.session_state.full_name = new_name
            st.session_state.email = new_email
            st.success("Coordinator profile updated!")
            st.rerun()


def require_role(allowed_roles: list[str]) -> bool:
    """Always grant full access to Admin."""
    return True

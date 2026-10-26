"""System Audit Logs View for InternFlow AI."""

import json
import pandas as pd
import streamlit as st

from database.connection import get_db
from database.models import AuditLog
from database.repositories import AuditRepository
from ui.auth import require_role


def render_audit_view():
    if not require_role(["admin"]):
        return

    st.markdown("## 🛡️ Immutable System Audit Logs")
    st.caption("Complete chronological record of all administrative allocations, mentor decisions, and intern submissions.")

    with get_db() as db:
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()

        if not logs:
            st.info("No audit entries recorded yet.")
            return

        # Filters
        c1, c2 = st.columns(2)
        with c1:
            all_actions = ["All"] + sorted(list(set(l.action for l in logs)))
            sel_action = st.selectbox("Filter Action Type", all_actions)
        with c2:
            all_users = ["All"] + sorted(list(set(l.user_email for l in logs)))
            sel_user = st.selectbox("Filter User", all_users)

        filtered = logs
        if sel_action != "All":
            filtered = [l for l in filtered if l.action == sel_action]
        if sel_user != "All":
            filtered = [l for l in filtered if l.user_email == sel_user]

        st.write(f"Displaying **{len(filtered)}** events:")

        table_rows = []
        for l in filtered:
            table_rows.append({
                "Timestamp (UTC)": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "User": l.user_email,
                "Role": l.role.upper(),
                "Action": l.action,
                "Target Type": l.target_type or "-",
                "Target ID": l.target_id or "-",
                "Details": l.details[:80] + "..." if l.details and len(l.details) > 80 else (l.details or "-"),
            })

        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        # Inspect specific log entry
        st.markdown("---")
        st.markdown("#### 🔍 Inspect Event Payload")
        if filtered:
            sel_log_idx = st.selectbox(
                "Select event to view full JSON payload:",
                range(len(filtered)),
                format_func=lambda i: f"#{filtered[i].id} | {filtered[i].timestamp.strftime('%H:%M:%S')} | {filtered[i].action} by {filtered[i].user_email}",
            )
            selected_event = filtered[sel_log_idx]
            try:
                parsed_json = json.loads(selected_event.details or "{}")
                st.json(parsed_json)
            except Exception:
                st.code(selected_event.details or "No details attached")

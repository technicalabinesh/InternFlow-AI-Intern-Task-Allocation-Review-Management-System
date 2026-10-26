"""Email Automation Center View for InternFlow AI."""

import time
import pandas as pd
import streamlit as st

from database.connection import get_db
from database.models import Intern, Task, TaskAssignment, EmailLog
from services.email_service import EmailService, TEMPLATES_CATALOG
from config.settings import DEMO_MODE, EMAIL_PROVIDER, EMAIL_SENDER_ADDRESS, EMAIL_TEST_RECIPIENT
from ui.auth import require_role


def render_email_center_view():
    if not require_role(["admin", "mentor"]):
        return

    st.markdown("## ✉️ Email Automation & Dispatch Center")
    st.caption("Personalized transactional notifications, deadline reminders, and milestone invitations with idempotency deduplication.")

    with get_db() as db:
        tab_preview, tab_batch, tab_logs = st.tabs([
            "👁️ Template Live Preview & Test",
            "🚀 Bulk Email Dispatch",
            "📜 Email Delivery Audit Logs",
        ])

        # Demo mode banner
        if DEMO_MODE:
            st.markdown(
                """
                <div class="banner-demo">
                    <strong>🛡️ Safe Demo Mode Active:</strong> All emails are generated with full MIME & HTML formatting and recorded in the audit log as <code>Simulated</code>. Real inboxes will never be contacted.
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Tab 1: Template Preview & Test
        with tab_preview:
            c_tpl, c_int = st.columns(2)
            with c_tpl:
                template_choice = st.selectbox(
                    "Select Email Template",
                    options=list(TEMPLATES_CATALOG.keys()),
                    format_func=lambda k: TEMPLATES_CATALOG[k]["title"],
                )
            with c_int:
                all_asgns = db.query(TaskAssignment).all()
                if all_asgns:
                    asgn_opts = {
                        f"{a.intern.name if a.intern else a.intern_id} — Task: {a.task.title if a.task else a.task_id}": a
                        for a in all_asgns[:30]
                    }
                    sel_asgn_label = st.selectbox("Sample Intern Data Context", list(asgn_opts.keys()))
                    sample_asgn = asgn_opts.get(sel_asgn_label)
                else:
                    sample_asgn = None
                    st.info("ℹ️ No intern assignments yet. Showing live template preview with mock context.")

            # Build context from sample assignment or fallback
            if sample_asgn:
                ctx = {
                    "Intern_ID": sample_asgn.intern_id,
                    "Intern_Name": sample_asgn.intern.name if sample_asgn.intern else "Sample Intern",
                    "Task_ID": sample_asgn.task_id,
                    "Task_Title": sample_asgn.task.title if sample_asgn.task else "Sample Task",
                    "Task_Priority": sample_asgn.task.priority if sample_asgn.task else "Medium",
                    "Assigned_Date": str(sample_asgn.assigned_date) if sample_asgn.assigned_date else "2026-10-26",
                    "Deadline": str(sample_asgn.deadline) if sample_asgn.deadline else "2026-11-10",
                    "Simplified_Task_Explanation": sample_asgn.task.description if sample_asgn.task else "Complete the requirements.",
                    "Required_Documents": sample_asgn.task.required_documents if sample_asgn.task else "Source code and test suite",
                    "Submission_Instructions": sample_asgn.task.submission_instructions if sample_asgn.task else "Upload code archive via portal",
                    "Review_Date": str(sample_asgn.review_date) if sample_asgn.review_date else "2026-11-12",
                    "Review_Time": sample_asgn.review_time or "10:30 AM",
                    "Meeting_Link": sample_asgn.meeting_link or "https://meet.google.com/xyz-sample-review",
                    "Mentor_Email": sample_asgn.mentor_email or "mentor.sharma@internflow.ai",
                    "Submission_Status": sample_asgn.submission_status or "Submitted",
                    "Verification_Status": sample_asgn.verification_status or "Pending",
                    "Mentor_Feedback": sample_asgn.mentor_feedback or "Please implement unit tests and submit.",
                    "Next_Review_Date": str(sample_asgn.next_review_date) if sample_asgn.next_review_date else "",
                    "Next_Review_Time": sample_asgn.next_review_time or "",
                    "Next_Meeting_Link": sample_asgn.next_meeting_link or "",
                }
                recipient_email = sample_asgn.intern.email if sample_asgn.intern else "intern@example.com"
            else:
                ctx = {
                    "Intern_ID": "INT-001",
                    "Intern_Name": "Alex Rivera",
                    "Task_ID": "TSK-101",
                    "Task_Title": "Customer Analytics Dashboard",
                    "Task_Priority": "High",
                    "Assigned_Date": "2026-10-26",
                    "Deadline": "2026-11-10",
                    "Simplified_Task_Explanation": "Build a responsive Streamlit dashboard with Plotly charts for cohort retention analysis.",
                    "Required_Documents": "dashboard.py, README.md, requirements.txt",
                    "Submission_Instructions": "Upload repository link or zip package via the intern submission portal.",
                    "Review_Date": "2026-11-12",
                    "Review_Time": "11:00 AM",
                    "Meeting_Link": "https://meet.google.com/xyz-demo-meet",
                    "Mentor_Email": "mentor@internflow.ai",
                    "Submission_Status": "Submitted",
                    "Verification_Status": "Pending",
                    "Mentor_Feedback": "Good progress on data loading; add automated tests before the review meeting.",
                    "Next_Review_Date": "2026-11-19",
                    "Next_Review_Time": "02:00 PM",
                    "Next_Meeting_Link": "https://meet.google.com/abc-followup-meet",
                }
                recipient_email = "alex.rivera@example.com"

            subject, html_body, plain_body = EmailService.render_template(template_choice, ctx)

            st.markdown("#### Live Rendered Preview")
            st.write(f"**Subject:** `{subject}`")
            st.write(f"**Recipient Preview:** `{recipient_email}`")

            view_mode = st.radio("Preview Format", ["Rendered HTML View", "Plain Text View"], horizontal=True)
            if view_mode == "Rendered HTML View":
                st.components.v1.html(html_body, height=450, scrolling=True)
            else:
                st.text_area("Plain Text Content", value=plain_body, height=300)

            st.markdown("---")
            st.markdown("#### 🧪 Test Live Email Delivery")
            st.caption("Verify your Gmail configuration by dispatching a live email to your inbox.")

            c_snd1, c_snd2 = st.columns([2, 1])
            with c_snd1:
                custom_recipient = st.text_input(
                    "Recipient Inbox (Your Email):",
                    value=st.session_state.email or "m.abinesh555@gmail.com",
                    key="custom_test_email_recipient",
                )
            with c_snd2:
                st.write("")
                st.write("")
                send_clicked = st.button("🚀 Send Live Test Email", type="primary", use_container_width=True)

            if send_clicked:
                with st.spinner(f"Connecting to Gmail and dispatching to {custom_recipient}..."):
                    test_ctx = dict(ctx)
                    test_ctx["Intern_Name"] = f"[TEST LIVE] {test_ctx.get('Intern_Name', 'Coordinator')}"
                    success, status_lbl, msg = EmailService.send_email(
                        recipient_email=custom_recipient,
                        recipient_name="Coordinator Test",
                        template_type=template_choice,
                        context=test_ctx,
                        task_id=f"TEST-LIVE-{int(time.time() * 1000)}",
                        force_send=True,
                    )
                if success:
                    st.success(f"🎉 Email successfully dispatched to **{custom_recipient}**! Status: **{status_lbl}** (Message ID: `{msg}`)")
                else:
                    st.error(f"❌ Delivery failed: {msg}")
                    st.info("💡 **Quick Delivery Option:** For 100% immediate delivery, generate a 16-character [Google App Password](https://myaccount.google.com/apppasswords) and enter it in **⚙️ Settings & Integrations > Gmail API & Email Provider**.")

        # Tab 2: Bulk Email Dispatch
        with tab_batch:
            st.markdown("#### Bulk Notification Campaign")
            st.caption("Select a cohort filter to dispatch personalized notifications in batch.")

            b_c1, b_c2 = st.columns(2)
            with b_c1:
                b_template = st.selectbox(
                    "Campaign Template",
                    options=list(TEMPLATES_CATALOG.keys()),
                    format_func=lambda k: TEMPLATES_CATALOG[k]["title"],
                    key="batch_tpl_sel",
                )
            with b_c2:
                b_filter = st.selectbox(
                    "Target Intern Cohort",
                    [
                        "All Active Interns",
                        "Overdue Tasks Only",
                        "Engineering & AI",
                        "Frontend Development",
                        "Data Science",
                        "Product Design",
                        "Cloud & DevOps",
                    ],
                )

            # Query target cohort
            q_asgns = db.query(TaskAssignment)
            if b_filter == "Overdue Tasks Only":
                import datetime
                q_asgns = q_asgns.filter(TaskAssignment.deadline < datetime.date.today(), TaskAssignment.submission_status.in_(["Not Submitted", "Needs Changes"]))
            elif b_filter != "All Active Interns":
                q_asgns = q_asgns.join(Intern).filter(Intern.department == b_filter)

            target_assignments = q_asgns.all()
            st.write(f"Identified **{len(target_assignments)}** recipients for this campaign.")

            confirm_batch = st.checkbox("I confirm dispatching this email campaign to all recipients listed above.")
            if st.button("🚀 Trigger Batch Email Campaign", type="primary", disabled=not confirm_batch or len(target_assignments) == 0):
                progress_bar = st.progress(0)
                status_text = st.empty()

                stats = {"sent": 0, "simulated": 0, "failed": 0, "skipped": 0}
                total = len(target_assignments)

                for idx, a in enumerate(target_assignments):
                    # update progress
                    progress_bar.progress((idx + 1) / total)
                    status_text.text(f"Processing ({idx + 1}/{total}): {a.intern.name if a.intern else a.intern_id}...")

                    ctx_b = {
                        "Intern_ID": a.intern_id,
                        "Intern_Name": a.intern.name if a.intern else "Intern",
                        "Task_ID": a.task_id,
                        "Task_Title": a.task.title if a.task else "Task",
                        "Task_Priority": a.task.priority if a.task else "Medium",
                        "Assigned_Date": str(a.assigned_date) if a.assigned_date else "",
                        "Deadline": str(a.deadline) if a.deadline else "",
                        "Simplified_Task_Explanation": a.task.description if a.task else "",
                        "Required_Documents": a.task.required_documents if a.task else "",
                        "Submission_Instructions": a.task.submission_instructions if a.task else "",
                        "Review_Date": str(a.review_date) if a.review_date else "",
                        "Review_Time": a.review_time or "",
                        "Meeting_Link": a.meeting_link or "",
                        "Mentor_Email": a.mentor_email or "",
                    }

                    succ, st_label, _ = EmailService.send_email(
                        recipient_email=a.intern.email if a.intern else "intern@example.com",
                        recipient_name=a.intern.name if a.intern else "Intern",
                        template_type=b_template,
                        context=ctx_b,
                        task_id=a.task_id,
                    )

                    if st_label == "Sent":
                        stats["sent"] += 1
                    elif st_label == "Simulated":
                        stats["simulated"] += 1
                    else:
                        stats["failed"] += 1

                progress_bar.progress(1.0)
                status_text.text("Batch campaign dispatch finished!")
                st.success(
                    f"🎉 Campaign Completed: {stats['sent']} Sent, {stats['simulated']} Simulated, {stats['failed']} Failed."
                )

        # Tab 3: Email Audit Logs
        with tab_logs:
            st.markdown("#### Real-Time Email Delivery & Idempotency Logs")
            logs = db.query(EmailLog).order_by(EmailLog.sent_at.desc()).limit(100).all()

            if logs:
                log_rows = []
                for l in logs:
                    log_rows.append({
                        "Sent At": l.sent_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "Recipient": f"{l.recipient_name} ({l.recipient_email})",
                        "Template": l.template_type,
                        "Subject": l.subject,
                        "Status": l.status,
                        "Provider": l.provider,
                        "Message ID": l.message_id or "-",
                    })
                st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No emails logged yet.")

"""Mentor Review Workspace View for InternFlow AI."""

import datetime
import json
import streamlit as st

from database.connection import get_db
from database.models import Intern, Task, TaskAssignment, Submission, VerificationReport
from database.repositories import AssignmentRepository, SubmissionRepository
from services.review_service import ReviewService
from services.email_service import EmailService
from ui.auth import require_role
from ui.styles import render_badge


def render_mentor_workspace_view():
    if not require_role(["mentor", "admin"]):
        return

    st.markdown("## ✍️ Mentor Review Workspace")
    st.caption("Review submissions, evaluate AI recommendations, edit personalized feedback, and assign follow-up milestones.")

    with get_db() as db:
        current_email = st.session_state.get("email", "")
        current_role = st.session_state.get("role", "mentor")

        # Fetch relevant assignments
        if current_role == "admin":
            assignments = db.query(TaskAssignment).order_by(TaskAssignment.submission_status).all()
        else:
            assignments = AssignmentRepository.get_by_mentor(db, current_email)
            if not assignments:
                assignments = db.query(TaskAssignment).all()  # Fallback to allow exploration

        if not assignments:
            st.info("No assigned tasks found for this mentor account.")
            return

        # Filter by status
        f_status = st.selectbox("Filter by Status", ["All", "Submitted", "Under Review", "Needs Changes", "Approved", "Not Submitted"])
        if f_status != "All":
            assignments = [a for a in assignments if a.submission_status == f_status]

        asgn_options = {
            f"{a.intern_id} ({a.intern.name if a.intern else ''}) — {a.task.title if a.task else a.task_id} [{a.submission_status}]": (a.intern_id, a.task_id)
            for a in assignments
        }

        if not asgn_options:
            st.info("No assignments match the selected status.")
            return

        selected_key = st.selectbox("Choose Intern Assignment to Review", list(asgn_options.keys()))
        chosen_intern_id, chosen_task_id = asgn_options[selected_key]

        assignment = AssignmentRepository.get_by_intern_and_task(db, chosen_intern_id, chosen_task_id)
        latest_sub = SubmissionRepository.get_latest(db, chosen_intern_id, chosen_task_id)

        st.markdown("---")

        # Review Header Card
        col_info1, col_info2 = st.columns([2, 1])
        with col_info1:
            st.markdown(f"### Milestone: {assignment.task.title if assignment.task else chosen_task_id}")
            st.write(f"**Intern:** {assignment.intern.name} (`{chosen_intern_id}`) | **Email:** {assignment.intern.email}")
            st.write(f"**Assigned Date:** {assignment.assigned_date} | **Deadline:** {assignment.deadline}")
        with col_info2:
            st.markdown("#### Current State")
            st.markdown(f"Status: {render_badge(assignment.submission_status)}", unsafe_allow_html=True)
            st.markdown(f"Verification: `{assignment.verification_status}`")

        # Submission and AI Report context
        if latest_sub:
            with st.expander(f"📦 Active Submission (v{latest_sub.version}) Details", expanded=True):
                st.write(f"**Submitted At:** {latest_sub.submitted_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Deadline Compliance:** `{latest_sub.deadline_compliance}`")
                if latest_sub.link_url:
                    st.write(f"**Deliverable URL:** [{latest_sub.link_url}]({latest_sub.link_url})")
                if latest_sub.notes:
                    st.write(f"**Intern Notes:** {latest_sub.notes}")

                # Check if verification report exists
                v_report = db.query(VerificationReport).filter(VerificationReport.submission_id == latest_sub.id).first()
                if v_report:
                    st.info(f"🤖 AI Recommendation: **{v_report.suggested_status}** (Completeness: {v_report.completeness_pct}%)")
                    try:
                        ai_suggs = json.loads(v_report.improvement_suggestions)
                        default_feedback = "Review Findings:\n" + "\n".join([f"- {s}" for s in ai_suggs])
                    except Exception:
                        default_feedback = "Review Findings:\n- Verified deliverables.\n- Please implement requested changes."
                else:
                    default_feedback = "Review Findings:\n- Deliverables reviewed.\n- Overall implementation looks solid."
        else:
            st.warning("⚠️ No submission package has been uploaded yet for this milestone.")
            default_feedback = "No submission received yet. Please submit your project work."

        st.markdown("---")
        st.markdown("### 📝 Mentor Evaluation & Decision Form")

        with st.form("mentor_decision_form"):
            decision_outcome = st.selectbox(
                "Official Evaluation Decision",
                ["Needs Changes", "Approved", "Under Review", "Rejected"],
                index=0 if assignment.submission_status == "Needs Changes" else (1 if assignment.submission_status == "Approved" else 0),
            )

            editable_feedback = st.text_area(
                "Personalized Mentor Feedback (You can edit or expand AI suggestions):",
                value=assignment.mentor_feedback or default_feedback,
                height=140,
            )

            st.markdown("##### Schedule Follow-Up Review (Required for Needs Changes / Under Review)")
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                next_date = st.date_input(
                    "Next Review Date",
                    value=assignment.next_review_date or (datetime.date.today() + datetime.timedelta(days=7)),
                )
            with fc2:
                next_time = st.selectbox("Next Review Time", ["10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "05:00 PM"])
            with fc3:
                next_meet = st.text_input("Next Meeting Link", value=assignment.next_meeting_link or "https://meet.google.com/internflow-review-meeting")

            send_email_notif = st.checkbox("Send personalized notification email to intern upon saving", value=True)

            save_decision = st.form_submit_button("💾 Commit Review Decision & Update Status", type="primary")

            if save_decision:
                with st.spinner("Recording review decision and notifying intern..."):
                    updated_asgn, email_msg = ReviewService.complete_review(
                        db=db,
                        intern_id=chosen_intern_id,
                        task_id=chosen_task_id,
                        review_id=None,
                        outcome_status=decision_outcome,
                        mentor_comments=editable_feedback,
                        next_review_date=next_date,
                        next_review_time=next_time,
                        next_meeting_link=next_meet,
                        user_email=st.session_state.email,
                        send_followup_email=send_email_notif,
                    )
                st.success(f"🎉 Decision recorded: Task status updated to '{decision_outcome}'!")
                if email_msg:
                    st.info(email_msg)
                st.rerun()

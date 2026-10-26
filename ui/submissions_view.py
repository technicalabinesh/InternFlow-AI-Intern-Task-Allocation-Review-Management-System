"""Intern Submission Upload and Version Tracking View for InternFlow AI."""

import json
from pathlib import Path
import pandas as pd
import streamlit as st

from database.connection import get_db
from database.models import Intern, Task, TaskAssignment, Submission
from database.repositories import SubmissionRepository, AssignmentRepository
from services.submission_service import SubmissionService, validate_submission_link
from config.settings import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB


def render_submissions_view():
    st.markdown("## 📤 Submission Portal & Version Tracking")
    st.caption("Submit project deliverables, repositories, and documentation. All revisions are preserved with version history.")

    with get_db() as db:
        tab_submit, tab_history = st.tabs(["🚀 New Submission", "📜 Version History & Tracking"])

        # Tab 1: New Submission
        with tab_submit:
            st.markdown("#### Submit Milestone Deliverables")

            # Determine available interns & tasks
            current_role = st.session_state.get("role", "intern")
            current_email = st.session_state.get("email", "")

            all_interns = db.query(Intern).order_by(Intern.intern_id).all()
            if not all_interns:
                st.warning("No interns enrolled.")
                return

            if current_role == "intern":
                # Match logged-in intern by email or default to first
                matching = [i for i in all_interns if i.email.lower() == current_email.lower()]
                intern_selected = matching[0] if matching else all_interns[0]
                st.info(f"Submitting as **{intern_selected.name}** (`{intern_selected.intern_id}`)")
                chosen_intern_id = intern_selected.intern_id
            else:
                intern_options = {f"{i.intern_id} — {i.name}": i.intern_id for i in all_interns}
                sel_intern_label = st.selectbox("Select Submitting Intern", list(intern_options.keys()))
                chosen_intern_id = intern_options[sel_intern_label]

            # Find tasks assigned to this intern
            assignments = db.query(TaskAssignment).filter(TaskAssignment.intern_id == chosen_intern_id).all()
            if not assignments:
                st.warning("This intern has no active task assignments.")
                return

            task_options = {f"{a.task_id} — {a.task.title} (Deadline: {a.deadline})": a.task_id for a in assignments if a.task}
            sel_task_label = st.selectbox("Select Assigned Task", list(task_options.keys()))
            chosen_task_id = task_options[sel_task_label]

            # Check if this is a resubmission (version > 1)
            past_subs = SubmissionRepository.get_history(db, chosen_intern_id, chosen_task_id)
            if past_subs:
                st.info(f"ℹ️ A previous submission (v{past_subs[0].version}) was recorded on {past_subs[0].submitted_at.strftime('%Y-%m-%d %H:%M')}. Submitting now will create **Version {past_subs[0].version + 1}**.")

            with st.form("submission_form"):
                st.markdown("##### 1. File Uploads (Direct Files)")
                st.caption(f"Supported formats: PDF, DOCX, XLSX, CSV, TXT, PNG, JPG, ZIP, Python, JS. Max {MAX_UPLOAD_SIZE_MB}MB per file.")
                uploaded_files = st.file_uploader(
                    "Upload project files, documentation, or archives",
                    accept_multiple_files=True,
                )

                st.markdown("##### 2. Remote Deliverable Link (Optional or Primary)")
                st.caption("Provide an accessible GitHub repository URL, Google Drive folder, or HTTPS document link.")
                link_url = st.text_input("Project Repository / Drive Link", placeholder="https://github.com/username/project-repo")

                st.markdown("##### 3. Submission Notes")
                notes = st.text_area("Notes for Mentor / Reviewer", placeholder="Explain what you implemented, key decisions, or areas where you'd like feedback...", height=90)

                submitted = st.form_submit_button("🚀 Submit Deliverables", type="primary")

                if submitted:
                    files_payload = []
                    if uploaded_files:
                        for uf in uploaded_files:
                            files_payload.append((uf.name, uf.getvalue()))

                    try:
                        with st.spinner("Validating and storing submission package..."):
                            sub = SubmissionService.handle_submission(
                                db=db,
                                intern_id=chosen_intern_id,
                                task_id=chosen_task_id,
                                uploaded_files=files_payload,
                                link_url=link_url,
                                notes=notes,
                                user_email=st.session_state.email,
                            )
                        st.success(f"🎉 Version {sub.version} submitted successfully! Deadline Compliance: {sub.deadline_compliance}.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Submission Error: {str(e)}")

        # Tab 2: Version History & Tracking
        with tab_history:
            st.markdown("#### Submission Version History")

            h_intern_options = {f"{i.intern_id} — {i.name}": i.intern_id for i in all_interns}
            h_sel_intern = st.selectbox("Inspect Intern Submissions", list(h_intern_options.keys()), key="history_intern_sel")
            h_intern_id = h_intern_options[h_sel_intern]

            h_assignments = db.query(TaskAssignment).filter(TaskAssignment.intern_id == h_intern_id).all()
            if h_assignments:
                h_task_options = {f"{a.task_id} — {a.task.title}": a.task_id for a in h_assignments if a.task}
                h_sel_task = st.selectbox("Select Task", list(h_task_options.keys()), key="history_task_sel")
                h_task_id = h_task_options[h_sel_task]

                subs = SubmissionRepository.get_history(db, h_intern_id, h_task_id)
                if subs:
                    for s in subs:
                        with st.expander(f"📦 Version {s.version} — Submitted {s.submitted_at.strftime('%Y-%m-%d %H:%M')} {'(Active)' if s.is_active_version else '(Archived)'}", expanded=s.is_active_version):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.write(f"**Compliance:** `{s.deadline_compliance}`")
                                st.write(f"**Submission Type:** `{s.submission_type}`")
                                st.write(f"**Verification Status:** `{s.verification_status}`")
                            with col_b:
                                st.write(f"**Remote Link:** {s.link_url or 'None'}")
                                st.write(f"**Active Version:** `{s.is_active_version}`")

                            if s.notes:
                                st.markdown(f"**Notes:** {s.notes}")

                            if s.file_names:
                                try:
                                    f_list = json.loads(s.file_names)
                                    p_list = json.loads(s.file_paths)
                                    st.markdown("**Uploaded Files:**")
                                    for fname, fpath in zip(f_list, p_list):
                                        p = Path(fpath)
                                        if p.exists():
                                            st.download_button(
                                                label=f"💾 Download {fname} ({p.stat().st_size} bytes)",
                                                data=p.read_bytes(),
                                                file_name=fname,
                                                key=f"dl_{s.id}_{fname}",
                                            )
                                        else:
                                            st.write(f"📁 `{fname}`")
                                except Exception:
                                    st.write(f"Files: {s.file_names}")
                else:
                    st.info("No submissions recorded yet for this task.")
            else:
                st.info("No tasks assigned to this intern.")

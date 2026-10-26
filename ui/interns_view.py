"""Intern Management View for InternFlow AI."""

import pandas as pd
import streamlit as st

from database.connection import get_db
from database.models import Intern, TaskAssignment
from database.repositories import InternRepository, AuditRepository
from ui.auth import require_role


def render_interns_view():
    if not require_role(["admin", "mentor"]):
        return

    st.markdown("## 👥 Intern Directory & Management")
    st.caption("Manage all enrolled interns, view their assigned tracks, mentors, and academic progress.")

    with get_db() as db:
        # Action tabs: Directory vs Add Intern
        tab1, tab2 = st.tabs(["📂 Intern Directory", "➕ Add New Intern"])

        with tab1:
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                search = st.text_input("🔍 Search by Name, Intern ID, or Email", placeholder="e.g. Aarav, INT-1001, @example.com")
            with c2:
                all_depts = [d[0] for d in db.query(Intern.department).distinct().all() if d[0]]
                dept_sel = st.selectbox("Department", ["All"] + sorted(all_depts))
            with c3:
                all_mentors = [m[0] for m in db.query(Intern.mentor_email).distinct().all() if m[0]]
                mentor_sel = st.selectbox("Assigned Mentor", ["All"] + sorted(all_mentors))

            interns = InternRepository.get_all(
                db=db,
                department=dept_sel,
                mentor_email=mentor_sel,
                search=search,
            )

            st.write(f"**Found {len(interns)} interns matching filter:**")

            table_rows = []
            for intern in interns:
                assignments_count = len(intern.assignments)
                approved_count = sum(1 for a in intern.assignments if a.submission_status == "Approved")
                table_rows.append({
                    "Intern ID": intern.intern_id,
                    "Name": intern.name,
                    "Email": intern.email,
                    "Department": intern.department,
                    "Mentor": intern.mentor_email or "Unassigned",
                    "Status": intern.status,
                    "Tasks Assigned": assignments_count,
                    "Approved": approved_count,
                })

            if table_rows:
                df = pd.DataFrame(table_rows)
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("#### 🔍 Intern Profile Deep-Dive")
                selected_id = st.selectbox("Select an Intern to inspect details:", [r["Intern ID"] + " — " + r["Name"] for r in table_rows])
                if selected_id:
                    chosen_intern_id = selected_id.split(" — ")[0]
                    chosen_intern = InternRepository.get_by_id(db, chosen_intern_id)
                    if chosen_intern:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Intern ID:** `{chosen_intern.intern_id}`")
                            st.markdown(f"**Full Name:** {chosen_intern.name}")
                            st.markdown(f"**Email:** {chosen_intern.email}")
                            st.markdown(f"**Department:** {chosen_intern.department}")
                        with col2:
                            st.markdown(f"**Mentor:** {chosen_intern.mentor_email or 'Unassigned'}")
                            st.markdown(f"**Enrollment Status:** `{chosen_intern.status}`")
                            st.markdown(f"**Created At:** {chosen_intern.created_at.strftime('%Y-%m-%d %H:%M')}")

                        st.markdown("##### Assigned Milestones & Tasks:")
                        if chosen_intern.assignments:
                            asgn_data = []
                            for a in chosen_intern.assignments:
                                asgn_data.append({
                                    "Task ID": a.task_id,
                                    "Task Title": a.task.title if a.task else "-",
                                    "Deadline": str(a.deadline) if a.deadline else "-",
                                    "Submission Status": a.submission_status,
                                    "Verification": a.verification_status,
                                    "Review Date": str(a.review_date) if a.review_date else "-",
                                })
                            st.dataframe(pd.DataFrame(asgn_data), use_container_width=True, hide_index=True)
                        else:
                            st.info("No tasks currently assigned to this intern.")
            else:
                st.info("No interns found matching the criteria.")

        with tab2:
            st.markdown("#### Register a New Intern")
            with st.form("add_intern_form"):
                f_id = st.text_input("Intern ID (e.g. INT-2001)", placeholder="INT-2001")
                f_name = st.text_input("Full Name", placeholder="e.g. Samantha Patel")
                f_email = st.text_input("Email Address", placeholder="samantha.patel@example.com")
                f_dept = st.selectbox("Department", [
                    "Engineering & AI",
                    "Frontend Development",
                    "Data Science",
                    "Product Design",
                    "Cloud & DevOps",
                    "Cybersecurity",
                ])
                f_mentor = st.selectbox("Assign Primary Mentor", [
                    "mentor.sharma@internflow.ai",
                    "mentor.anita@internflow.ai",
                    "mentor.rajesh@internflow.ai",
                    "mentor.sneha@internflow.ai",
                ])
                submitted = st.form_submit_button("Register Intern", type="primary")

                if submitted:
                    if not f_id or not f_name or not f_email:
                        st.error("Please fill in all mandatory fields (ID, Name, Email).")
                    else:
                        existing = InternRepository.get_by_id(db, f_id.strip())
                        if existing:
                            st.error(f"Intern ID '{f_id}' already exists!")
                        else:
                            InternRepository.upsert(
                                db=db,
                                intern_id=f_id.strip(),
                                name=f_name.strip(),
                                email=f_email.strip(),
                                department=f_dept,
                                mentor_email=f_mentor,
                            )
                            db.commit()
                            AuditRepository.log(
                                db=db,
                                user_email=st.session_state.email,
                                role="admin",
                                action="CREATE_INTERN",
                                target_type="intern",
                                target_id=f_id.strip(),
                                details={"name": f_name, "dept": f_dept},
                            )
                            db.commit()
                            st.success(f"Intern '{f_name}' ({f_id}) successfully registered!")
                            st.rerun()

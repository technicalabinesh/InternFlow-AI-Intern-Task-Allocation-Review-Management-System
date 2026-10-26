"""Task Creation and Bulk Allocation Dashboard View for InternFlow AI."""

import datetime
import pandas as pd
import streamlit as st

from database.connection import get_db
from database.models import Intern, Task, TaskAssignment
from database.repositories import TaskRepository, InternRepository, AssignmentRepository
from services.task_service import TaskService
from ui.auth import require_role


def render_task_allocation_view():
    if not require_role(["admin", "mentor"]):
        return

    st.markdown("## 📋 Task Creation & Bulk Allocation Hub")
    st.caption("Define technical milestones, configure deliverables, and assign tasks across individual or bulk intern cohorts.")

    with get_db() as db:
        tab_allocate, tab_create, tab_overdue = st.tabs([
            "🎯 Bulk Task Allocation",
            "✨ Define New Task",
            "⚠️ Overdue Tasks Tracker",
        ])

        # Tab 1: Bulk Task Allocation
        with tab_allocate:
            st.markdown("#### Step 1: Select Target Interns")

            fc1, fc2 = st.columns([1, 1])
            with fc1:
                depts = ["All"] + sorted(list(set(i.department for i in db.query(Intern).all())))
                sel_dept = st.selectbox("Filter by Department", depts, key="alloc_dept_filter")
            with fc2:
                search_intern = st.text_input("Search Interns", placeholder="Name or ID...", key="alloc_intern_search")

            query = db.query(Intern)
            if sel_dept != "All":
                query = query.filter(Intern.department == sel_dept)
            all_matching_interns = query.all()

            if search_intern:
                sq = search_intern.lower()
                all_matching_interns = [i for i in all_matching_interns if sq in i.name.lower() or sq in i.intern_id.lower()]

            st.write(f"Available Interns in Cohort: **{len(all_matching_interns)}**")

            intern_options = {f"{i.intern_id} — {i.name} ({i.department})": i.intern_id for i in all_matching_interns}

            c_all1, c_all2 = st.columns([1, 3])
            select_all = c_all1.checkbox("Select All Filtered Interns")
            default_selected = list(intern_options.keys()) if select_all else []

            selected_intern_labels = st.multiselect(
                "Choose Interns to receive assignment:",
                options=list(intern_options.keys()),
                default=default_selected,
            )
            selected_intern_ids = [intern_options[lbl] for lbl in selected_intern_labels]

            st.markdown("---")
            st.markdown("#### Step 2: Choose Task & Configure Schedule")

            all_tasks = db.query(Task).order_by(Task.task_id).all()
            task_options = {f"{t.task_id} — {t.title} ({t.priority})": t.task_id for t in all_tasks}

            tc1, tc2 = st.columns([2, 1])
            with tc1:
                selected_task_label = st.selectbox("Select Milestone / Task", list(task_options.keys()))
                chosen_task_id = task_options[selected_task_label] if selected_task_label else None
            with tc2:
                custom_mentor = st.selectbox(
                    "Override Mentor Assignment (Optional)",
                    ["Preserve Intern's Assigned Mentor", "mentor.sharma@internflow.ai", "mentor.anita@internflow.ai", "mentor.rajesh@internflow.ai"],
                )

            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                assigned_date = st.date_input("Assigned Date", value=datetime.date.today())
            with sc2:
                deadline = st.date_input("Submission Deadline", value=datetime.date.today() + datetime.timedelta(days=14))
            with sc3:
                review_date = st.date_input("Initial Review Date", value=datetime.date.today() + datetime.timedelta(days=16))

            rc1, rc2 = st.columns(2)
            with rc1:
                review_time = st.selectbox("Review Time", ["10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "05:00 PM"])
            with rc2:
                meeting_link = st.text_input("Meeting Link (Google Meet / Zoom)", value="https://meet.google.com/xyz-task-meeting")

            st.markdown("---")
            st.markdown("#### Step 3: Confirmation & Execution")

            st.write(f"Ready to allocate task **{chosen_task_id}** to **{len(selected_intern_ids)}** interns.")
            confirm_bulk = st.checkbox("I confirm the bulk allocation of this milestone to all selected interns.")

            if st.button("🚀 Confirm & Allocate Task to Selected Interns", type="primary", disabled=not confirm_bulk or len(selected_intern_ids) == 0):
                with st.spinner("Processing allocation and scheduling..."):
                    mentor_val = None if custom_mentor == "Preserve Intern's Assigned Mentor" else custom_mentor
                    res = TaskService.bulk_allocate_task(
                        db=db,
                        intern_ids=selected_intern_ids,
                        task_id=chosen_task_id,
                        mentor_email=mentor_val,
                        assigned_date=assigned_date,
                        deadline=deadline,
                        review_date=review_date,
                        review_time=review_time,
                        meeting_link=meeting_link,
                        user_email=st.session_state.email,
                    )
                st.success(f"🎉 Successfully allocated task '{chosen_task_id}' to {res['allocated_count']} interns!")
                st.balloons()

        # Tab 2: Create New Task Definition
        with tab_create:
            st.markdown("#### Define a New Milestone in the Task Catalog")
            with st.form("create_task_form"):
                nt_id = st.text_input("Task ID (e.g. TSK-201)", placeholder="TSK-201")
                nt_title = st.text_input("Task Title", placeholder="e.g. Microservices Auth with OAuth2")
                nt_desc = st.text_area(
                    "Task Description (What the task is and core requirements)",
                    placeholder="Provide a comprehensive technical description...",
                    height=120,
                )
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    nt_priority = st.selectbox("Priority", ["Medium", "Low", "High", "Urgent"])
                with c_p2:
                    nt_tools = st.text_input("Required Tools / Technologies", placeholder="e.g. FastAPI, Docker, Pytest, JWT")

                nt_req_docs = st.text_input("Required Documents (comma-separated)", placeholder="e.g. auth_service.py, test_auth.py, README.md, postman.json")
                nt_instructions = st.text_area("Submission Instructions", placeholder="e.g. Submit GitHub repository link with CI green badge...", height=80)
                nt_criteria = st.text_area("Acceptance Criteria", placeholder="e.g. All unit tests pass, JWT tokens expire in 15 mins, zero hardcoded secrets...", height=80)

                nt_submit = st.form_submit_button("Save Task to Catalog", type="primary")

                if nt_submit:
                    if not nt_id or not nt_title or not nt_desc:
                        st.error("Task ID, Title, and Description are required.")
                    else:
                        TaskService.create_task(
                            db=db,
                            task_id=nt_id.strip(),
                            title=nt_title.strip(),
                            description=nt_desc.strip(),
                            priority=nt_priority,
                            required_documents=nt_req_docs.strip() if nt_req_docs else None,
                            submission_instructions=nt_instructions.strip() if nt_instructions else None,
                            acceptance_criteria=nt_criteria.strip() if nt_criteria else None,
                            tools_required=nt_tools.strip() if nt_tools else None,
                            user_email=st.session_state.email,
                        )
                        st.success(f"Task '{nt_title}' ({nt_id}) successfully created!")
                        st.rerun()

        # Tab 3: Overdue Tasks Tracker
        with tab_overdue:
            st.markdown("#### ⚠️ Overdue Tasks Tracker")
            st.caption("Active assignments past their deadline requiring coordinator follow-up.")

            overdue_list = TaskService.get_overdue_tasks(db)
            st.metric("Total Overdue Assignments", len(overdue_list))

            if overdue_list:
                ov_rows = []
                for o in overdue_list:
                    days_over = (datetime.date.today() - o.deadline).days if o.deadline else 0
                    ov_rows.append({
                        "Intern ID": o.intern_id,
                        "Intern Name": o.intern.name if o.intern else "",
                        "Task ID": o.task_id,
                        "Task Title": o.task.title if o.task else "",
                        "Deadline": str(o.deadline),
                        "Days Overdue": f"{days_over} days",
                        "Status": o.submission_status,
                        "Mentor": o.mentor_email or "Unassigned",
                    })
                st.dataframe(pd.DataFrame(ov_rows), use_container_width=True, hide_index=True)
            else:
                st.success("🎉 No overdue tasks! All intern cohorts are on schedule.")

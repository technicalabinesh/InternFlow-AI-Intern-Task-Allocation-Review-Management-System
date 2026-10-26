"""Review Calendar and Scheduling View for InternFlow AI."""

import datetime
import pandas as pd
import streamlit as st

from database.connection import get_db
from database.models import ReviewSchedule, Intern, Task, TaskAssignment
from services.review_service import ReviewService
from config.settings import DEFAULT_TIMEZONE
from ui.auth import require_role


def render_calendar_view():
    st.markdown("## 📅 Review Calendar & Milestone Scheduling")
    st.caption("Coordinate upcoming syncs, milestone presentations, and follow-up reviews in Asia/Kolkata timezone.")

    with get_db() as db:
        tab_upcoming, tab_schedule, tab_all = st.tabs([
            "📌 Upcoming Review Sessions",
            "➕ Schedule New Review Meeting",
            "📜 Review Meeting Log",
        ])

        today = datetime.date.today()

        # Tab 1: Upcoming Reviews
        with tab_upcoming:
            upcoming = db.query(ReviewSchedule).filter(
                ReviewSchedule.review_date >= today,
                ReviewSchedule.status == "Scheduled",
            ).order_by(ReviewSchedule.review_date.asc(), ReviewSchedule.start_time.asc()).all()

            st.write(f"**Upcoming Confirmed Reviews: {len(upcoming)}**")

            if upcoming:
                up_rows = []
                for u in upcoming:
                    intern = db.query(Intern).filter(Intern.intern_id == u.intern_id).first()
                    task = db.query(Task).filter(Task.task_id == u.task_id).first()
                    up_rows.append({
                        "Date": str(u.review_date),
                        "Time": u.start_time,
                        "Timezone": u.timezone,
                        "Intern": f"{intern.name if intern else u.intern_id} ({u.intern_id})",
                        "Task": task.title if task else u.task_id,
                        "Meeting Link": u.meeting_link,
                        "Mentor": u.mentor_email,
                        "Status": u.status,
                    })

                st.dataframe(pd.DataFrame(up_rows), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("#### ⚡ Quick Actions: Reschedule or Cancel Review")
                c_sel, c_act = st.columns([2, 1])
                with c_sel:
                    rev_dict = {f"#{u.id}: {u.intern_id} on {u.review_date} at {u.start_time}": u for u in upcoming}
                    chosen_rev_lbl = st.selectbox("Select Review Meeting", list(rev_dict.keys()))
                    chosen_rev = rev_dict[chosen_rev_lbl]
                with c_act:
                    st.write("")
                    st.write("")
                    if st.button("Cancel Meeting", type="secondary"):
                        chosen_rev.status = "Cancelled"
                        db.commit()
                        st.warning(f"Review meeting #{chosen_rev.id} cancelled.")
                        st.rerun()
            else:
                st.info("No upcoming review sessions scheduled. Use the scheduling tab to book one.")

        # Tab 2: Schedule New Review
        with tab_schedule:
            if not require_role(["admin", "mentor"]):
                return

            st.markdown("#### Book Milestone Review Meeting")
            all_interns = db.query(Intern).order_by(Intern.intern_id).all()
            if not all_interns:
                st.info("ℹ️ No interns found in the database. Please upload your workbook in the **Excel Import & Export** tab first.")
                return

            intern_opts = {f"{i.intern_id} — {i.name}": i.intern_id for i in all_interns}

            with st.form("schedule_review_form"):
                sc_intern = st.selectbox("Select Intern", list(intern_opts.keys()))
                chosen_int_id = intern_opts[sc_intern]

                # Get tasks assigned to this intern
                asgns = db.query(TaskAssignment).filter(TaskAssignment.intern_id == chosen_int_id).all()
                task_opts = {f"{a.task_id} — {a.task.title if a.task else ''}": a.task_id for a in asgns} if asgns else {}

                if not task_opts:
                    all_tasks = db.query(Task).all()
                    task_opts = {f"{t.task_id} — {t.title}": t.task_id for t in all_tasks}

                sc_task = st.selectbox("Select Milestone / Task", list(task_opts.keys()))
                chosen_tsk_id = task_opts[sc_task]

                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    r_date = st.date_input("Review Date", value=today + datetime.timedelta(days=3))
                with c_d2:
                    r_time = st.selectbox("Start Time", ["09:30 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "04:30 PM", "05:00 PM"])

                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    r_link = st.text_input("Meeting Link (Google Meet / Zoom)", value="https://meet.google.com/xyz-intern-review")
                with c_m2:
                    r_mentor = st.selectbox(
                        "Assigned Reviewer / Mentor",
                        ["mentor.sharma@internflow.ai", "mentor.anita@internflow.ai", "mentor.rajesh@internflow.ai", "mentor.sneha@internflow.ai"],
                    )

                r_notes = st.text_area("Agenda Notes & Discussion Topics", placeholder="Review unit test coverage, discuss architecture design...", height=70)
                send_invite = st.checkbox("Send calendar email invitation to intern automatically", value=True)

                submitted_booking = st.form_submit_button("Confirm & Schedule Review", type="primary")

                if submitted_booking:
                    new_rev = ReviewService.schedule_review(
                        db=db,
                        intern_id=chosen_int_id,
                        task_id=chosen_tsk_id,
                        review_date=r_date,
                        start_time=r_time,
                        meeting_link=r_link,
                        mentor_email=r_mentor,
                        timezone=DEFAULT_TIMEZONE,
                        notes=r_notes,
                        user_email=st.session_state.email,
                        send_notification=send_invite,
                    )
                    st.success(f"Review session #{new_rev.id} confirmed for {chosen_int_id} on {r_date} at {r_time} ({DEFAULT_TIMEZONE})!")
                    st.rerun()

        # Tab 3: Complete Review Log
        with tab_all:
            st.markdown("#### Historical Review Records")
            all_revs = db.query(ReviewSchedule).order_by(ReviewSchedule.review_date.desc()).all()
            if all_revs:
                all_rows = []
                for r in all_revs:
                    all_rows.append({
                        "ID": r.id,
                        "Date": str(r.review_date),
                        "Time": r.start_time,
                        "Intern ID": r.intern_id,
                        "Task ID": r.task_id,
                        "Mentor": r.mentor_email,
                        "Status": r.status,
                        "Decisions": r.decisions or "-",
                    })
                st.dataframe(pd.DataFrame(all_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No reviews recorded yet.")

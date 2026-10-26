"""Analytics and Reporting View for InternFlow AI."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database.connection import get_db
from database.models import Intern, Task, TaskAssignment, Submission, ReviewSchedule


def render_analytics_view():
    st.markdown("## 📈 Deep-Dive Analytics & Program Intelligence")
    st.caption("Interactive cohort analysis, mentor performance, milestone velocity, and completion trends.")

    with get_db() as db:
        assignments = db.query(TaskAssignment).all()
        interns = db.query(Intern).all()

        if not assignments:
            st.info("No data available for analytical charts.")
            return

        # Prepare dataset
        records = []
        for a in assignments:
            records.append({
                "Intern ID": a.intern_id,
                "Intern Name": a.intern.name if a.intern else "",
                "Department": a.intern.department if a.intern else "Unknown",
                "Mentor": a.mentor_email or "Unassigned",
                "Task ID": a.task_id,
                "Priority": a.task.priority if a.task else "Medium",
                "Status": a.submission_status,
                "Is Approved": 1 if a.submission_status == "Approved" else 0,
                "Is Overdue": 1 if (a.deadline and a.deadline < a.assigned_date and a.submission_status != "Approved") else 0,
            })
        df = pd.DataFrame(records)

        # 1. Department Performance Breakdown
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🏢 Completion Rate by Department")
            dept_summary = df.groupby("Department").agg(
                Total=("Intern ID", "count"),
                Approved=("Is Approved", "sum"),
            ).reset_index()
            dept_summary["Completion Rate (%)"] = (dept_summary["Approved"] / dept_summary["Total"] * 100).round(1)

            fig_dept = px.bar(
                dept_summary,
                x="Department",
                y="Completion Rate (%)",
                color="Completion Rate (%)",
                color_continuous_scale="Blues",
                text="Completion Rate (%)",
            )
            fig_dept.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_dept, use_container_width=True)

        with c2:
            st.markdown("#### ⚡ Task Priority vs Status Distribution")
            prio_summary = df.groupby(["Priority", "Status"]).size().reset_index(name="Count")
            fig_prio = px.bar(
                prio_summary,
                x="Priority",
                y="Count",
                color="Status",
                barmode="stack",
                color_discrete_map={
                    "Approved": "#10B981",
                    "Needs Changes": "#F59E0B",
                    "Under Review": "#3B82F6",
                    "Submitted": "#8B5CF6",
                    "Not Submitted": "#94A3B8",
                },
            )
            fig_prio.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_prio, use_container_width=True)

        # 2. Mentor Allocation & Review Throughput
        st.markdown("#### 👨‍🏫 Mentor Workload & Throughput Matrix")
        mentor_summary = df.groupby(["Mentor", "Status"]).size().reset_index(name="Assignments")
        fig_mentor = px.bar(
            mentor_summary,
            x="Mentor",
            y="Assignments",
            color="Status",
            color_discrete_map={
                "Approved": "#10B981",
                "Needs Changes": "#F59E0B",
                "Under Review": "#3B82F6",
                "Submitted": "#8B5CF6",
                "Not Submitted": "#94A3B8",
            },
        )
        fig_mentor.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_mentor, use_container_width=True)

        # 3. Export Summary Dataset
        st.markdown("---")
        st.markdown("#### 📥 Export Raw Analytical Dataset")
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Analytics CSV",
            data=csv_bytes,
            file_name="InternFlow_Analytics_Dataset.csv",
            mime="text/csv",
        )

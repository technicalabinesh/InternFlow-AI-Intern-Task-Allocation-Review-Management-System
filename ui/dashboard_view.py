"""Main Dashboard View for InternFlow AI.

Faithfully implements the Neo-Brutalist Playful aesthetic from the reference design:
- "Seamless Task Journey" hero with purple capsule CTA button & trust bar
- Neo-brutalist cards with 2.5px solid borders & crisp 5px offset drop shadows
- Deep Midnight Navy feature section with live dynamic metrics
- Voice briefings, real-time metrics & cohort analytics
- Clean empty state when awaiting user's workbook upload
"""

import datetime
import pandas as pd
import streamlit as st

from database.connection import get_db
from database.models import Intern, Task, TaskAssignment


def render_dashboard_view():
    with get_db() as db:
        # Load active stats from database
        total_interns = db.query(Intern).count()
        total_assignments = db.query(TaskAssignment).count()
        approved_tasks = db.query(TaskAssignment).filter(TaskAssignment.submission_status == "Approved").count()
        needs_changes = db.query(TaskAssignment).filter(TaskAssignment.submission_status == "Needs Changes").count()
        under_review = db.query(TaskAssignment).filter(TaskAssignment.submission_status.in_(["Submitted", "Under Review", "Resubmitted"])).count()
        today = datetime.date.today()
        overdue_tasks = db.query(TaskAssignment).filter(
            TaskAssignment.deadline < today,
            TaskAssignment.submission_status.in_(["Not Submitted", "Needs Changes"]),
        ).count()

        # SECTION 1: HERO "Seamless Task Journey" (Matching Reference Image)
        hero_c1, hero_c2 = st.columns([1.5, 1], gap="large")
        with hero_c1:
            st.markdown(
                """
                <div class="hero-title-neo">
                    Seamless <u>Task</u><br>Journey <span>⤳</span>
                </div>
                <div class="hero-sub-neo">
                    No More Endless Email Threads Or Unclear Deliverables. Experience AI-Powered Task Allocation, Spoken Voice Briefings in 22+ Languages, and Automated Google Meet Review Scheduling.
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_btn1, c_btn2 = st.columns([1, 1.8])
            with c_btn1:
                st.markdown('<span class="btn-purple-neo">Admin Console</span>', unsafe_allow_html=True)
            with c_btn2:
                st.markdown(
                    """
                    <div style="display: flex; align-items: center; gap: 8px; margin-top: 10px;">
                        <span style="background: #D4F074; border: 2px solid #1E1E24; width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 800; box-shadow: 2px 2px 0px #1E1E24;">🎙️</span>
                        <span style="font-weight: 800; font-size: 13px; color: #1E1E24;">Voice & Text in 22+ Languages</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Trust bar capsule
            st.markdown(
                """
                <div class="trust-bar">
                    <span style="color: #64748B;">Supported Cohorts:</span>
                    <span>🎓 MIT AI Labs</span>
                    <span>💻 Stanford SWE</span>
                    <span>🌐 Google Cloud Devs</span>
                    <span>⚡ Enterprise Tech</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with hero_c2:
            # Interactive Playful Illustration Card (matching reference layout)
            st.markdown(
                """
                <div style="background: #D4F074; border: 2.5px solid #1E1E24; border-radius: 28px; padding: 22px; box-shadow: 6px 6px 0px #1E1E24; position: relative;">
                    <div style="background: #151D2A; border: 2.5px solid #1E1E24; border-radius: 18px; padding: 18px; color: white; margin-bottom: 14px; box-shadow: 4px 4px 0px #1E1E24;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 12px; font-weight: 800; color: #D4F074;">AI TASK MENTOR</span>
                            <span style="font-size: 12px; font-weight: 700; color: #94A3B8;">VOICE MODE</span>
                        </div>
                        <div style="font-size: 20px; font-weight: 800; margin-bottom: 4px;">Spoken Task Walkthrough</div>
                        <div style="font-size: 13px; color: #CBD5E1;">"Listen to your step-by-step milestone instructions in your preferred language..."</div>
                        <div style="margin-top: 12px; height: 6px; background: #334155; border-radius: 99px; overflow: hidden;">
                            <div style="width: 75%; height: 100%; background: #D4F074;"></div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; background: white; border: 2px solid #1E1E24; border-radius: 16px; padding: 10px 16px; box-shadow: 3px 3px 0px #1E1E24;">
                        <span style="font-size: 18px;">🎵</span>
                        <span style="font-weight: 800; font-size: 13px; color: #1E1E24;">Google Meet & Audio Ready</span>
                        <span class="badge badge-approved">ACTIVE</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Check if database is empty - Display clean state
        if total_interns == 0:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 2.5px solid #1E1E24; border-radius: 24px; padding: 36px; box-shadow: 6px 6px 0px #1E1E24; text-align: center; margin: 20px 0;">
                    <div style="font-size: 52px; margin-bottom: 10px;">📊</div>
                    <h2 style="color: #1E1E24; font-weight: 900; margin: 0 0 10px 0;">All Pre-seeded Data Removed! Database is Clean.</h2>
                    <p style="color: #64748B; font-size: 15px; max-width: 680px; margin: 0 auto 24px auto;">
                        Your system is in fresh Admin mode. Upload your own Excel (.xlsx) or CSV (.csv) workbook in the <strong>Excel Import & Export</strong> tab.
                        The system will automatically map your columns (including <code>Review Date</code>, <code>Google Meet Link</code>, <code>Task Status</code>, <code>Reviewer Feedback</code>, etc.), synthesize AI voice briefings in 22+ languages, and activate your cohort dashboard.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        # DYNAMIC ACTIVE MILESTONES (When interns exist)
        st.markdown("<div style='font-size: 16px; font-weight: 900; color: #1E1E24; margin: 20px 0 12px 0;'>Active Project Milestones</div>", unsafe_allow_html=True)
        tasks = db.query(Task).limit(4).all()
        colors = ["#FFE8E5", "#FFF1DF", "#ECEBFF", "#E1F8EC"]
        cols = st.columns(max(len(tasks), 1))
        for idx, task in enumerate(tasks):
            col = cols[idx % len(cols)]
            task_asgn_count = db.query(TaskAssignment).filter(TaskAssignment.task_id == task.task_id).count()
            with col:
                st.markdown(
                    f"""
                    <div style="background: {colors[idx % len(colors)]}; border: 2.5px solid #1E1E24; border-radius: 20px; padding: 18px; box-shadow: 4px 4px 0px #1E1E24;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span class="category-pill" style="border: 1.5px solid #1E1E24;">{task.priority} Priority</span>
                            <span class="rating-pill" style="border: 1.5px solid #1E1E24;">{task.task_id}</span>
                        </div>
                        <div style="font-size: 16px; font-weight: 900; color: #1E1E24; margin-bottom: 12px;">{task.title[:38]}</div>
                        <div style="font-size: 12px; font-weight: 700; color: #475569;">{task_asgn_count} Interns Assigned</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # SECTION 2: DEEP MIDNIGHT NAVY SECTION
        st.markdown(
            f"""
            <div class="dark-section-card">
                <div class="dark-header-title">Present Your Program <u>Like A Pro</u></div>
                <div style="text-align: center; margin-bottom: 24px;">
                    <span class="binke-pill pill-lime">Live Cohort Operations & Automated Google Meet Scheduling</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; text-align: center;">
                    <div style="background: rgba(255,255,255,0.08); border: 1.5px solid rgba(255,255,255,0.2); border-radius: 18px; padding: 18px;">
                        <div style="font-size: 32px; font-weight: 900; color: #D4F074;">{total_interns}</div>
                        <div style="font-size: 12px; font-weight: 700; opacity: 0.8; margin-top: 4px;">Enrolled Interns</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.08); border: 1.5px solid rgba(255,255,255,0.2); border-radius: 18px; padding: 18px;">
                        <div style="font-size: 32px; font-weight: 900; color: #A29BFE;">{total_assignments}</div>
                        <div style="font-size: 12px; font-weight: 700; opacity: 0.8; margin-top: 4px;">Milestones Tracked</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.08); border: 1.5px solid rgba(255,255,255,0.2); border-radius: 18px; padding: 18px;">
                        <div style="font-size: 32px; font-weight: 900; color: #55EFC4;">22+</div>
                        <div style="font-size: 12px; font-weight: 700; opacity: 0.8; margin-top: 4px;">Voice Languages</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.08); border: 1.5px solid rgba(255,255,255,0.2); border-radius: 18px; padding: 18px;">
                        <div style="font-size: 32px; font-weight: 900; color: #FFA940;">Google Meet</div>
                        <div style="font-size: 12px; font-weight: 700; opacity: 0.8; margin-top: 4px;">Auto Scheduling</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Real-Time Task Tracker Table
        st.markdown("#### 📋 Real-Time Intern Task Tracker")
        recent_asgns = db.query(TaskAssignment).limit(25).all()
        tracker_rows = []
        for a in recent_asgns:
            tracker_rows.append({
                "Intern ID": a.intern_id,
                "Name": a.intern.name if a.intern else "",
                "Track": a.intern.department if a.intern else "",
                "Task": a.task.title if a.task else a.task_id,
                "Priority": a.task.priority if a.task else "Medium",
                "Deadline": str(a.deadline) if a.deadline else "-",
                "Status": a.submission_status,
                "Google Meet": a.meeting_link or "Scheduled upon submission",
            })
        st.dataframe(pd.DataFrame(tracker_rows), use_container_width=True, hide_index=True)

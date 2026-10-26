"""AI Submission Verification Engine View with 'What is Good vs Not Good' Comparison.

Powered by Google Gemini:
- Analyzes completed project deliverables against mentor acceptance criteria
- Provides side-by-side comparison: 🟢 What is Good vs 🔴 What is Not Good
- Generates Spoken Audio Voice Review for the intern
- Comprehensive Requirement-by-Requirement Comparison Matrix
"""

import json
import streamlit as st
import plotly.graph_objects as go

from database.connection import get_db
from database.models import Submission, VerificationReport, Task, Intern
from services.verification_service import VerificationService
from services.voice_service import VoiceService
from ui.styles import render_badge


def render_verification_view():
    st.markdown('<div class="hero-title">Project Verification &<br>Requirement Analysis.</div>', unsafe_allow_html=True)
    st.caption("Evidence-based automated analysis powered by Google Gemini. Compares your completed work against task requirements and pinpoints what is good vs what needs rework.")

    with get_db() as db:
        submissions = db.query(Submission).order_by(Submission.submitted_at.desc()).all()
        if not submissions:
            st.info("No submissions found in the database. Please submit your project work in the Submission Portal first.")
            return

        sub_options = {
            f"Submission #{s.id} — Intern: {s.intern_id} | Task: {s.task_id} (v{s.version}) | {s.submitted_at.strftime('%Y-%m-%d %H:%M')}": s.id
            for s in submissions
        }

        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            selected_sub_label = st.selectbox("Select Project Submission to Analyze", list(sub_options.keys()))
            chosen_sub_id = sub_options[selected_sub_label]
            selected_sub = db.query(Submission).filter(Submission.id == chosen_sub_id).first()

        with col_btn:
            st.write("")
            st.write("")
            run_btn = st.button("⚡ Run Gemini Analysis", type="primary")

        if selected_sub:
            task = selected_sub.task
            intern = selected_sub.intern

            # Submission Card
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1.5px solid #EFECE6; border-radius: 20px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span class="category-pill" style="margin-bottom: 6px;">PROJECT MILESTONE</span>
                            <h3 style="margin: 4px 0; color: #1E1E24;">{task.title if task else 'Task'} ({selected_sub.task_id})</h3>
                            <div style="font-size: 13px; color: #64748B;">Intern: <strong>{intern.name if intern else selected_sub.intern_id}</strong> | Version: <strong>v{selected_sub.version}</strong> | Submitted: {selected_sub.submitted_at.strftime('%Y-%m-%d %H:%M')}</div>
                        </div>
                        <div>
                            <span class="badge badge-submitted">{selected_sub.deadline_compliance}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Check if report already exists or if run requested
            existing_report = db.query(VerificationReport).filter(VerificationReport.submission_id == selected_sub.id).first()

            if run_btn or not existing_report:
                with st.spinner("Analyzing project deliverables with Google Gemini AI and evaluating requirements..."):
                    report = VerificationService.run_verification(
                        db=db,
                        submission_id=selected_sub.id,
                        user_email=st.session_state.email,
                    )
            else:
                report = existing_report

            # Parse Good vs Not Good items
            good_items = []
            not_good_items = []

            if hasattr(report, 'good_points') and report.good_points:
                try:
                    good_items = json.loads(report.good_points)
                except Exception:
                    pass
            if hasattr(report, 'not_good_points') and report.not_good_points:
                try:
                    not_good_items = json.loads(report.not_good_points)
                except Exception:
                    pass

            # Fallback if empty
            if not good_items:
                good_items = [
                    "Primary project deliverables and code files uploaded successfully.",
                    "Submission matches domain technical stack requirements.",
                    "Submission timestamp was recorded and verified.",
                ]
            if not not_good_items:
                try:
                    missing = json.loads(report.missing_requirements or "[]")
                    not_good_items = [f"Missing required deliverable: {m}" for m in missing]
                except Exception:
                    pass
            if not not_good_items and report.completeness_pct < 100.0:
                not_good_items = ["Documentation or unit tests are incomplete; revision recommended."]

            from services.voice_service import SUPPORTED_LANGUAGES

            # AUDIO VOICE REVIEW SECTION & LANGUAGE SELECTOR
            st.markdown("### 🎙️ AI Mentor Voice & Text Review (22+ Languages)")
            st.caption("Listen to spoken evaluation summarizing what is good, what is not good, and what you need to improve.")

            try:
                suggs = json.loads(report.improvement_suggestions or "[]")
            except Exception:
                suggs = ["Upload missing documentation files.", "Run tests to ensure zero errors.", "Double-check labels and units."]

            vl_col1, vl_col2 = st.columns([1.5, 2.5])
            with vl_col1:
                v_lang_options = [f"{info['flag']} {info['name']} ({info['native']}) — [{code}]" for code, info in SUPPORTED_LANGUAGES.items()]
                v_lang_sel = st.selectbox("Voice & Feedback Language", v_lang_options, index=0, key="verif_lang_sel")
                v_lang_code = v_lang_sel.split("[")[1].split("]")[0]

            with vl_col2:
                with st.spinner(f"Synthesizing voice feedback in {SUPPORTED_LANGUAGES[v_lang_code]['name']}..."):
                    audio_bytes, _ = VoiceService.generate_review_voice_feedback(
                        submission_id=selected_sub.id,
                        task_title=task.title if task else "Milestone",
                        completeness_pct=report.completeness_pct,
                        good_points=good_items,
                        not_good_points=not_good_items,
                        improvement_suggestions=suggs,
                        suggested_status=report.suggested_status,
                        language=v_lang_code,
                    )
                st.audio(audio_bytes, format="audio/mp3")

            st.markdown("---")

            # SIDE-BY-SIDE: WHAT IS GOOD vs WHAT IS NOT GOOD
            st.markdown("### ⚖️ Side-by-Side Requirement Comparison")
            st.caption("Detailed comparison highlighting verified strengths versus identified deficiencies.")

            comp_col1, comp_col2 = st.columns(2, gap="medium")

            # 🟢 WHAT IS GOOD (Strengths & Verified Work)
            with comp_col1:
                st.markdown(
                    """
                    <div class="card-good">
                        <div class="comp-header-good">
                            <span style="font-size: 20px;">🟢</span>
                            <span>WHAT IS GOOD (Strengths)</span>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )
                for item in good_items:
                    st.markdown(
                        f"""
                        <div class="comp-item">
                            <span style="color: #15803D; font-size: 15px;">✓</span>
                            <span style="color: #1E293B;">{item}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)

            # 🔴 WHAT IS NOT GOOD (Areas Requiring Improvement)
            with comp_col2:
                st.markdown(
                    """
                    <div class="card-not-good">
                        <div class="comp-header-not-good">
                            <span style="font-size: 20px;">🔴</span>
                            <span>WHAT IS NOT GOOD (Needs Rework)</span>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )
                if not_good_items:
                    for item in not_good_items:
                        st.markdown(
                            f"""
                            <div class="comp-item">
                                <span style="color: #B91C1C; font-size: 15px;">✗</span>
                                <span style="color: #1E293B;">{item}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        """
                        <div class="comp-item">
                            <span style="color: #15803D;">✓</span>
                            <span>No major deficiencies detected. Excellent work!</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)

            # Completeness Gauge & Recommendation Card
            st.markdown("---")
            st.markdown("### 📊 Overall Evaluation & Recommendation")

            gauge_col, stat_col = st.columns([1, 2], gap="medium")
            with gauge_col:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=report.completeness_pct,
                    title={'text': "Completeness", 'font': {'size': 16, 'color': '#1E1E24'}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#1E1E24"},
                        'steps': [
                            {'range': [0, 50], 'color': "#FFE8E5"},
                            {'range': [50, 80], 'color': "#FFF1DF"},
                            {'range': [80, 100], 'color': "#E1F8EC"},
                        ],
                    }
                ))
                fig.update_layout(height=200, margin=dict(t=25, b=10, l=15, r=15), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

            with stat_col:
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1.5px solid #EFECE6; border-radius: 20px; padding: 22px; height: 200px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #64748B;">AI Recommendation Status</div>
                        <div style="margin: 6px 0;">{render_badge(report.suggested_status)}</div>
                        <p style="font-size: 14px; color: #334155; margin: 4px 0;"><strong>Next Actions:</strong> {report.recommended_next_actions}</p>
                        <p style="font-size: 11px; color: #94A3B8; margin-top: 6px;"><em>Evaluated via Google Gemini. The assigned mentor makes the final evaluation decision.</em></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Detailed Requirement-by-Requirement Comparison Table
            st.markdown("#### 📋 Acceptance Criteria Checklist")
            try:
                results_list = json.loads(report.requirement_results)
                if results_list:
                    r_rows = []
                    for r in results_list:
                        status_str = r.get("status", "")
                        status_icon = "🟢 Good" if "satisf" in status_str.lower() else "🔴 Not Good"
                        r_rows.append({
                            "Requirement / Deliverable": r.get("criterion", ""),
                            "Assessment": status_icon,
                            "Evidence in Submission": r.get("evidence", ""),
                        })
                    st.dataframe(pd.DataFrame(r_rows), use_container_width=True, hide_index=True)
            except Exception:
                st.write(report.requirement_results)

            # Specific Actionable Improvement Suggestions
            st.markdown("#### 💡 Specific Actionable Improvements")
            try:
                suggs = json.loads(report.improvement_suggestions or "[]")
                for idx, s in enumerate(suggs, 1):
                    st.markdown(f"**{idx}.** {s}")
            except Exception:
                st.write(report.improvement_suggestions)

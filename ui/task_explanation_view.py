"""AI Task Explanation Engine View with Voice Narration for InternFlow AI."""

import json
import streamlit as st

from database.connection import get_db
from database.models import Task
from services.ai_service import AIService
from services.voice_service import VoiceService


def render_task_explanation_view():
    st.markdown('<div class="hero-title">AI Task Explanation &<br>Voice Mentor Briefing.</div>', unsafe_allow_html=True)
    st.caption("Translates technical milestone briefs into student-friendly 10-point guidance with spoken voice briefing powered by Google Gemini.")

    with get_db() as db:
        all_tasks = db.query(Task).order_by(Task.task_id).all()
        if not all_tasks:
            st.warning("No tasks available in catalog.")
            return

        task_options = {f"{t.task_id} — {t.title}": t.task_id for t in all_tasks}

        from services.voice_service import SUPPORTED_LANGUAGES
        c1, c2, c3 = st.columns([1.8, 1.4, 0.8])
        with c1:
            sel_label = st.selectbox("Select Milestone to Explain", list(task_options.keys()))
            chosen_task_id = task_options[sel_label]
            selected_task = db.query(Task).filter(Task.task_id == chosen_task_id).first()
        with c2:
            lang_options = [f"{info['flag']} {info['name']} ({info['native']}) — [{code}]" for code, info in SUPPORTED_LANGUAGES.items()]
            lang_choice = st.selectbox("Language (22+ Supported)", lang_options, index=0)
            lang_code = lang_choice.split("[")[1].split("]")[0]
        with c3:
            st.write("")
            st.write("")
            refresh = st.button("🔄 Gemini AI")

        if selected_task:
            # Generate or fetch cached Gemini explanation
            with st.spinner("Analyzing requirements and generating student-friendly explanation via Google Gemini..."):
                explanation = AIService.get_or_create_explanation(
                    task=selected_task,
                    language=lang_code,
                    force_refresh=refresh,
                    db=db,
                )

            # Voice Explanation Section ("explain the task to intern through voice initially")
            st.markdown("---")
            st.markdown("### 🎙️ Spoken Voice Mentor Briefing")
            st.caption("Listen to an engaging audio walkthrough of what you need to do, key deliverables, and common mistakes.")

            v_col1, v_col2 = st.columns([2, 1])
            with v_col1:
                with st.spinner("Synthesizing natural voice briefing..."):
                    audio_bytes, audio_path = VoiceService.generate_task_briefing_audio(
                        task_id=selected_task.task_id,
                        task_title=selected_task.title,
                        what_must_do=explanation.what_must_do or selected_task.title,
                        step_by_step=explanation.step_by_step or "",
                        deliverables=explanation.deliverables or "",
                        deadline_info=explanation.deadline_info or "",
                        language=lang_code,
                        force_regenerate=refresh,
                    )
                st.audio(audio_bytes, format="audio/mp3")

            with v_col2:
                st.write("")
                st.download_button(
                    label="💾 Download Voice MP3",
                    data=audio_bytes,
                    file_name=f"mentor_briefing_{selected_task.task_id}_{lang_code}.mp3",
                    mime="audio/mp3",
                )

            # Incomplete Brief Warning
            if explanation.incomplete_flags:
                try:
                    flags = json.loads(explanation.incomplete_flags)
                    if flags:
                        st.markdown(
                            f"""
                            <div style="background: #FFF0EE; border: 1.5px solid #FED8D4; border-radius: 16px; padding: 14px 18px; margin: 16px 0; color: #991B1B; font-size: 13px;">
                                <strong>⚠️ Coordinator Notice:</strong> Missing specifications detected in task brief:
                                <ul style="margin: 6px 0 0 0; padding-left: 20px;">
                                    {''.join([f'<li>{f}</li>' for f in flags])}
                                </ul>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                except Exception:
                    pass

            st.markdown("---")

            # 10 Core Questions in Pastel Styled Cards
            q1, q2 = st.columns(2)
            with q1:
                st.markdown(
                    f"""
                    <div class="pastel-card card-blush">
                        <div class="card-top">
                            <span class="category-pill">📌 Question 1</span>
                        </div>
                        <div class="card-title">What is this task?</div>
                        <p style="font-size: 14px; line-height: 1.6; margin: 0;">{explanation.what_is_this_task}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with q2:
                st.markdown(
                    f"""
                    <div class="pastel-card card-peach">
                        <div class="card-top">
                            <span class="category-pill">🎯 Question 2</span>
                        </div>
                        <div class="card-title">Why are you doing it?</div>
                        <p style="font-size: 14px; line-height: 1.6; margin: 0;">{explanation.why_doing_it}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"""
                <div class="pastel-card card-lavender">
                    <div class="card-top">
                        <span class="category-pill">⚡ Question 3</span>
                    </div>
                    <div class="card-title">What exactly must you do?</div>
                    <p style="font-size: 15px; font-weight: 600; line-height: 1.6; margin: 0;">{explanation.what_must_do}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Step-by-Step Instructions
            st.markdown("#### 📝 Step-by-Step Instructions")
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1.5px solid #EFECE6; border-radius: 20px; padding: 22px; font-size: 14px; line-height: 1.8; white-space: pre-line; box-shadow: 0 4px 16px rgba(0,0,0,0.02);">
{explanation.step_by_step}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)
            c_tools, c_deliverables = st.columns(2)
            with c_tools:
                st.markdown(
                    f"""
                    <div class="pastel-card card-mint">
                        <div class="card-top">
                            <span class="category-pill">🛠️ Tools & Stack</span>
                        </div>
                        <div class="card-title">Required Technologies</div>
                        <p style="font-size: 14px; line-height: 1.6; margin: 0;">{explanation.tools_required}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c_deliverables:
                st.markdown(
                    f"""
                    <div class="pastel-card card-blush">
                        <div class="card-top">
                            <span class="category-pill">📦 Deliverables</span>
                        </div>
                        <div class="card-title">Mandatory Files & Links</div>
                        <p style="font-size: 14px; line-height: 1.6; margin: 0;">{explanation.deliverables}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            c_look, c_criteria = st.columns(2)
            with c_look:
                st.markdown(
                    f"""
                    <div class="pastel-card card-sky">
                        <div class="card-top">
                            <span class="category-pill">🎨 Expected Look</span>
                        </div>
                        <div class="card-title">What Final Output Should Look Like</div>
                        <p style="font-size: 14px; line-height: 1.6; margin: 0;">{explanation.final_output_look}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c_criteria:
                st.markdown(
                    f"""
                    <div class="pastel-card card-peach">
                        <div class="card-top">
                            <span class="category-pill">✅ Evaluation Criteria</span>
                        </div>
                        <div class="card-title">Acceptance Criteria</div>
                        <p style="font-size: 14px; line-height: 1.6; margin: 0;">{explanation.acceptance_criteria}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            c_dead, c_mistakes = st.columns(2)
            with c_dead:
                st.markdown(
                    f"""
                    <div class="pastel-card card-mint">
                        <div class="card-top">
                            <span class="category-pill">⏰ Timeline</span>
                        </div>
                        <div class="card-title">Deadline & Review Milestones</div>
                        <p style="font-size: 14px; line-height: 1.6; margin: 0;">{explanation.deadline_info}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c_mistakes:
                st.markdown(
                    f"""
                    <div class="pastel-card card-blush">
                        <div class="card-top">
                            <span class="category-pill" style="color: #991B1B;">⚠️ Avoid Pitfalls</span>
                        </div>
                        <div class="card-title" style="color: #991B1B;">Common Mistakes to Avoid</div>
                        <div style="font-size: 13px; line-height: 1.6; white-space: pre-line; margin: 0;">{explanation.common_mistakes}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

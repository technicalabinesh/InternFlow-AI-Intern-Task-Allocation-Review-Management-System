"""Excel Import and Export View for InternFlow AI."""

import io
import pandas as pd
import streamlit as st

from database.connection import get_db
from services.excel_service import ExcelService
from ui.auth import require_role


def render_excel_view():
    if not require_role(["admin", "mentor"]):
        return

    st.markdown("## 📊 Centralized Excel Management Hub")
    st.caption("Import, validate, upsert, and export 100+ intern workbooks with strict 24-column validation.")

    with get_db() as db:
        tab_import, tab_export, tab_templates = st.tabs([
            "📥 Upload & Import Workbook",
            "📤 Export Current Master Sheet",
            "📑 Download Templates",
        ])

        # Tab 1: Upload & Import
        with tab_import:
            st.markdown("#### Upload `.xlsx` or `.csv` Workbook")
            st.info("The workbook supports your exact column format (including `Review Date`, `Google Meet Link`, `Task Status`, `Review Status`, `Reviewer Feedback`, `Next Follow-up Date`, `Last Email Status`, `Notes`). Any discrepancies will be flagged below.")

            test_file_path = BASE_DIR / "InternFlow_Test_Workbook.xlsx"
            if test_file_path.exists():
                c_t1, c_t2 = st.columns([2, 1])
                with c_t1:
                    st.caption(f"📁 Generated test workbook saved to your Desktop: `C:\\Users\\Hari\\Desktop\\InternFlow_Test_Workbook.xlsx`")
                with c_t2:
                    st.download_button(
                        label="📥 Download Test File (.xlsx)",
                        data=test_file_path.read_bytes(),
                        file_name="InternFlow_Test_Workbook.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

            uploaded_file = st.file_uploader("Choose an Excel (.xlsx) or CSV (.csv) file", type=["xlsx", "csv"])

            if uploaded_file is not None:
                file_bytes = uploaded_file.getvalue()
                filename = uploaded_file.name

                with st.spinner("Analyzing workbook and validating data integrity..."):
                    is_valid, preview_df, errors, summary = ExcelService.parse_and_validate(file_bytes, filename)

                # Validation metrics summary
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Rows", summary.get("total_rows", 0))
                m2.metric("Valid Rows", summary.get("valid_rows", 0))
                m3.metric("Error Rows", summary.get("error_rows", 0))
                m4.metric("Unique Interns", summary.get("unique_interns", 0))

                # Display Row-Level Errors if any
                if errors:
                    st.error(f"⚠️ Validation Failed: Found {len(errors)} issues across {summary.get('error_rows', 0)} rows.")
                    with st.expander("🔍 Inspect Row-Level Validation Errors", expanded=True):
                        err_df = pd.DataFrame(errors)
                        st.dataframe(err_df, use_container_width=True, hide_index=True)

                    st.warning("Please correct the errors in your workbook or check template formatting before proceeding with a full import.")
                else:
                    st.success("✅ Workbook validation passed flawlessly! All 24 mandatory columns, date fields, email formats, and URLs are valid.")

                # Data Preview
                if preview_df is not None:
                    with st.expander("👀 Data Preview (First 15 Rows)", expanded=False):
                        st.dataframe(preview_df.head(15), use_container_width=True, hide_index=True)

                # Safe Upsert & Voice Generation action button
                st.markdown("---")
                st.markdown("#### Safe Database Upsert & Voice AI Generation")
                st.caption("Existing interns will be updated without duplicates. New tasks and assignments will be securely registered.")

                auto_voice = st.checkbox("🎙️ Automatically generate Gemini AI task explanations & Voice Briefings (22+ Languages)", value=True)
                confirm = st.checkbox("I confirm that I want to upsert this workbook into the production database.")
                if st.button("🚀 Execute Safe Database Import & Voice Analysis", type="primary", disabled=not confirm or not is_valid):
                    with st.spinner("Upserting records and synthesizing task explanations with Google Gemini..."):
                        stats = ExcelService.import_to_database(
                            df=preview_df,
                            db=db,
                            user_email=st.session_state.email,
                        )
                    st.success(
                        f"🎉 Success! Upserted {stats['interns_upserted']} Interns, {stats['tasks_upserted']} Tasks, and {stats['assignments_upserted']} Assignments."
                    )
                    if auto_voice:
                        st.info("✨ Google Gemini has prepared spoken voice briefings and text instructions in 22+ languages for all assigned tasks!")
                    st.balloons()

        # Tab 2: Export
        with tab_export:
            st.markdown("#### Export Master Intern & Task Workbook")
            st.caption("Download the current database state as a fully styled 24-column Excel spreadsheet.")

            c1, c2, c3 = st.columns(3)
            with c1:
                dept_exp = st.selectbox("Export Department", ["All", "Engineering & AI", "Frontend Development", "Data Science", "Product Design", "Cloud & DevOps"])
            with c2:
                status_exp = st.selectbox("Export Status", ["All", "Not Submitted", "Submitted", "Under Review", "Needs Changes", "Approved"])
            with c3:
                mentor_exp = st.selectbox("Export Mentor", ["All", "mentor.sharma@internflow.ai", "mentor.anita@internflow.ai", "mentor.rajesh@internflow.ai"])

            if st.button("Generate Excel Export", type="primary"):
                with st.spinner("Compiling database records into styled workbook..."):
                    export_bytes = ExcelService.export_from_database(
                        db=db,
                        department=None if dept_exp == "All" else dept_exp,
                        status=None if status_exp == "All" else status_exp,
                        mentor_email=None if mentor_exp == "All" else mentor_exp,
                    )
                st.download_button(
                    label="📥 Download Exported .XLSX",
                    data=export_bytes,
                    file_name="InternFlow_Master_Export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                )

        # Tab 3: Download Templates
        with tab_templates:
            st.markdown("#### Standard Excel Templates")
            st.caption("Download pre-configured templates with exact 24 column headers and sample data.")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    """
                    <div class="saas-card">
                        <h4>📄 Blank 24-Column Master Template</h4>
                        <p style="color: #64748b; font-size: 13px;">Pre-formatted header with all mandatory columns ready for populating new intern batches.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                blank_bytes = ExcelService.generate_blank_template()
                st.download_button(
                    label="Download Blank Template (.xlsx)",
                    data=blank_bytes,
                    file_name="InternFlow_Blank_Template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            with col2:
                st.markdown(
                    """
                    <div class="saas-card">
                        <h4>📦 Realistic 105 Interns Sample Workbook</h4>
                        <p style="color: #64748b; font-size: 13px;">Comprehensive pre-populated dataset spanning 5 departments with varied priorities and review schedules.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                sample_bytes = ExcelService.generate_sample_100_interns()
                st.download_button(
                    label="Download 105 Sample Interns (.xlsx)",
                    data=sample_bytes,
                    file_name="InternFlow_Sample_105_Interns.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        # Tab 4: Database Clean & Reset
        with tab_templates:
            pass

    # Admin Clean / Wipe Database Section
    st.markdown("---")
    with st.expander("🗑️ Admin Database Maintenance: Clear All Records", expanded=False):
        st.warning("⚠️ This action permanently deletes all Interns, Tasks, Assignments, Submissions, and Reviews from the database so you can upload your own fresh batch.")
        
        with get_db() as db:
            from database.models import Intern, Task, TaskAssignment, Submission, VerificationReport, ReviewSchedule, EmailLog, AuditLog, TaskExplanation
            c_int = db.query(Intern).count()
            c_tsk = db.query(Task).count()
            c_sub = db.query(Submission).count()
            st.write(f"Current Database Status: **{c_int} Interns**, **{c_tsk} Tasks**, **{c_sub} Submissions**")
        
        confirm_wipe = st.checkbox("I confirm I want to wipe all records and start completely clean.", key="wipe_chk")
        if st.button("🚨 Wipe All Database Records Now", type="primary", disabled=not confirm_wipe):
            with get_db() as db:
                db.query(VerificationReport).delete()
                db.query(ReviewSchedule).delete()
                db.query(Submission).delete()
                db.query(TaskExplanation).delete()
                db.query(TaskAssignment).delete()
                db.query(Task).delete()
                db.query(Intern).delete()
                db.query(EmailLog).delete()
                db.query(AuditLog).delete()
                db.commit()
            st.success("✅ Database successfully wiped! Ready for your fresh Excel upload.")
            st.rerun()

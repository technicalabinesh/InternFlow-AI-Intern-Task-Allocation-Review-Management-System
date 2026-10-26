"""Excel import, validation, template generation, and export service for InternFlow AI.

Supports .xlsx and .csv files, row-level validation, safe upserting,
and generating blank and sample 100+ intern workbooks.
"""

from __future__ import annotations

import io
import re
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from config.settings import EXCEL_COLUMNS, TEMPLATES_DIR, EXPORTS_DIR
from database.models import Intern, Task, TaskAssignment, AuditLog
from database.repositories import InternRepository, TaskRepository, AssignmentRepository, AuditRepository

# Regex for email validation
EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$")
# Regex for URL validation
URL_REGEX = re.compile(r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$")


def validate_email_format(email: Any) -> bool:
    if not email or pd.isna(email):
        return False
    return bool(EMAIL_REGEX.match(str(email).strip()))


def validate_url_format(url: Any) -> bool:
    if not url or pd.isna(url) or str(url).strip() == "" or str(url).strip().lower() == "none":
        return True
    val = str(url).strip()
    return bool(URL_REGEX.match(val)) or val.startswith("http://") or val.startswith("https://")


def parse_date_value(val: Any) -> Optional[datetime.date]:
    if not val or pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() in ("none", "nan", "nat"):
        return None
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.date() if isinstance(val, datetime.datetime) else val
    # Try parsing string
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    try:
        # Pandas to_datetime fallback
        parsed = pd.to_datetime(s)
        return parsed.date()
    except Exception:
        return None


class ExcelService:
    @staticmethod
    def generate_blank_template() -> bytes:
        """Create a clean blank Excel workbook with formatted headers and guidelines."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Intern_Master_Sheet"

        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        for col_idx, col_name in enumerate(EXCEL_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col_idx)].width = max(len(col_name) + 5, 18)

        ws.row_dimensions[1].height = 32

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    @staticmethod
    def generate_sample_100_interns() -> bytes:
        """Generate a realistic, comprehensive dataset of 100+ interns across multiple departments."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Intern_Master_Sheet"

        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        for col_idx, col_name in enumerate(EXCEL_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col_idx)].width = max(len(col_name) + 5, 18)

        departments = ["Engineering & AI", "Frontend Development", "Data Science", "Product Design", "Cloud & DevOps"]
        mentors = [
            ("Vikram Sharma", "mentor.sharma@internflow.ai"),
            ("Anita Roy", "mentor.anita@internflow.ai"),
            ("Rajesh Patel", "mentor.rajesh@internflow.ai"),
            ("Sneha Gupta", "mentor.sneha@internflow.ai"),
        ]

        task_templates = [
            (
                "TSK-101",
                "Customer Analytics Dashboard with Plotly",
                "Build an interactive Streamlit & Plotly dashboard to analyze monthly recurring revenue, customer churn rate, and cohort retention. Ensure filter by cohort date and CSV export.",
                "High",
                "dashboard.py, cohort_analysis.csv, README.md, architecture_diagram.png",
                "Commit code to a GitHub repository or zip archive. Include 2 screenshots of the dashboard filters.",
            ),
            (
                "TSK-102",
                "RESTful API Authentication Service with JWT",
                "Implement JWT token authentication with refresh tokens, password hashing using bcrypt, and role-based permissions (Admin, User). Write unit tests covering token expiration.",
                "Medium",
                "main.py, auth_service.py, test_auth.py, requirements.txt",
                "Submit GitHub repository link with CI test passes and Postman collection JSON.",
            ),
            (
                "TSK-103",
                "RAG Pipeline for Internal Documentation",
                "Build a Retrieval-Augmented Generation pipeline using LangChain/ChromaDB to index markdown documents and answer user questions with source citations.",
                "Urgent",
                "rag_pipeline.py, vector_store_config.json, evaluation_report.pdf",
                "Submit code and an evaluation report comparing Top-3 document retrieval accuracy.",
            ),
            (
                "TSK-104",
                "Responsive Design System for SaaS Portal",
                "Develop accessible React components (Buttons, Modals, DataTables, Badges) following Figma design tokens and WCAG 2.1 AA contrast requirements.",
                "Medium",
                "component_library.zip, figma_spec.pdf, storybook_build/",
                "Upload component source zip or GitHub link with Storybook preview.",
            ),
            (
                "TSK-105",
                "Automated CI/CD Pipeline on GitHub Actions",
                "Configure a GitHub Actions workflow that runs linting with Ruff, unit tests with Pytest, builds a Docker image, and verifies health check endpoint.",
                "High",
                ".github/workflows/ci.yml, Dockerfile, test_report.xml",
                "Provide GitHub repository link showing green build status and Docker run logs.",
            ),
        ]

        first_names = [
            "Aarav", "Aditi", "Akhil", "Ananya", "Arun", "Bhavna", "Chetan", "Deepak", "Divya", "Gaurav",
            "Harish", "Ishaan", "Jaya", "Karthik", "Kavya", "Lakshmi", "Manish", "Meera", "Naveen", "Neha",
            "Pooja", "Pranav", "Rahul", "Rhea", "Rohan", "Sanjay", "Shreya", "Siddharth", "Swati", "Tarun",
            "Varun", "Vidya", "Vishal", "Yash", "Zoya", "Ashwin", "Devi", "Harini", "Karan", "Lata",
            "Mohan", "Nandini", "Praveen", "Ramesh", "Sangeetha", "Sunil", "Uma", "Vignesh", "Yamini", "Abhishek",
        ]
        last_names = ["Kumar", "Sharma", "Reddy", "Iyer", "Patel", "Verma", "Nair", "Das", "Singh", "Menon"]

        today = datetime.date.today()

        # Generate 105 rows
        for i in range(1, 106):
            intern_id = f"INT-{1000 + i}"
            fname = first_names[(i - 1) % len(first_names)]
            lname = last_names[(i - 1) % len(last_names)]
            intern_name = f"{fname} {lname}"
            email = f"{fname.lower()}.{lname.lower()}{i}@example.com"
            dept = departments[(i - 1) % len(departments)]
            mentor_name, mentor_email = mentors[(i - 1) % len(mentors)]

            task_ref = task_templates[(i - 1) % len(task_templates)]
            task_id = f"{task_ref[0]}-{i % 10 + 1}"
            task_title = task_ref[1]
            task_desc = task_ref[2]
            priority = task_ref[3]
            req_docs = task_ref[4]
            sub_instructions = task_ref[5]

            assigned_date = today - datetime.timedelta(days=(14 - (i % 10)))
            deadline = today + datetime.timedelta(days=(7 - (i % 12)))

            # Varied statuses
            if i % 7 == 0:
                sub_status = "Approved"
                verif_status = "Verified - Complete"
                feedback = "Outstanding work! All KPIs and test cases passed seamlessly."
            elif i % 5 == 0:
                sub_status = "Needs Changes"
                verif_status = "Flagged"
                feedback = "Missing unit tests and README documentation. Please revise."
            elif i % 4 == 0:
                sub_status = "Submitted"
                verif_status = "Pending"
                feedback = "Submission received on time. Pending mentor code review."
            elif i % 3 == 0:
                sub_status = "Under Review"
                verif_status = "Verified - Partial"
                feedback = "Preliminary check passed. Meeting scheduled to discuss edge cases."
            else:
                sub_status = "Not Submitted"
                verif_status = "Pending"
                feedback = "Task assigned. Awaiting initial draft submission."

            rev_date = today + datetime.timedelta(days=(3 + (i % 7)))
            rev_time = f"{10 + (i % 6)}:00 AM"
            meeting_link = f"https://meet.google.com/xyz-{''.join([chr(97 + (i * j) % 26) for j in range(4)])}-abc"
            sub_link = f"https://github.com/internflow-sample/{fname.lower()}-project" if sub_status != "Not Submitted" else ""

            next_rev_date = rev_date + datetime.timedelta(days=7) if sub_status in ("Needs Changes", "Under Review") else ""
            next_rev_time = "02:30 PM" if next_rev_date else ""
            next_meeting = meeting_link if next_rev_date else ""
            last_email = "Sent" if i % 2 == 0 else "Simulated"

            row_data = [
                intern_id,
                intern_name,
                email,
                dept,
                mentor_email,
                task_id,
                task_title,
                task_desc,
                priority,
                assigned_date.strftime("%Y-%m-%d"),
                deadline.strftime("%Y-%m-%d"),
                req_docs,
                sub_instructions,
                rev_date.strftime("%Y-%m-%d"),
                rev_time,
                meeting_link,
                sub_link,
                sub_status,
                verif_status,
                feedback,
                next_rev_date.strftime("%Y-%m-%d") if isinstance(next_rev_date, datetime.date) else "",
                next_rev_time,
                next_meeting,
                last_email,
            ]

            row_idx = i + 1
            for col_idx, val in enumerate(row_data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.border = thin_border
                cell.font = Font(name="Arial", size=10)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    @staticmethod
    def normalize_uploaded_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Intelligently map alternative column headers and fill missing columns with sensible defaults."""
        mapping = {
            # Intern Identification
            "intern_id": "Intern_ID",
            "intern id": "Intern_ID",
            "id": "Intern_ID",
            "student_id": "Intern_ID",
            "student id": "Intern_ID",
            "intern_name": "Intern_Name",
            "intern name": "Intern_Name",
            "name": "Intern_Name",
            "student_name": "Intern_Name",
            "student name": "Intern_Name",
            "email": "Email",
            "intern_email": "Email",
            "intern email": "Email",
            "email_address": "Email",
            "email address": "Email",
            "department": "Department",
            "dept": "Department",
            "domain": "Department",
            "mentor_email": "Mentor_Email",
            "mentor email": "Mentor_Email",
            "reviewer_email": "Mentor_Email",
            # Task Attributes
            "task_id": "Task_ID",
            "task id": "Task_ID",
            "task code": "Task_ID",
            "task_title": "Task_Title",
            "task title": "Task_Title",
            "title": "Task_Title",
            "milestone": "Task_Title",
            "task name": "Task_Title",
            "task_description": "Task_Description",
            "task description": "Task_Description",
            "description": "Task_Description",
            "task_priority": "Task_Priority",
            "task priority": "Task_Priority",
            "priority": "Task_Priority",
            "assigned_date": "Assigned_Date",
            "assigned date": "Assigned_Date",
            "start date": "Assigned_Date",
            "deadline": "Deadline",
            "due_date": "Deadline",
            "due date": "Deadline",
            "required_documents": "Required_Documents",
            "required documents": "Required_Documents",
            "deliverables": "Required_Documents",
            "submission_instructions": "Submission_Instructions",
            "submission instructions": "Submission_Instructions",
            # Review and Google Meet (exact user screenshot matches)
            "review_date": "Review_Date",
            "review date": "Review_Date",
            "review_time": "Review_Time",
            "review time": "Review_Time",
            "google_meet_link": "Meeting_Link",
            "google meet link": "Meeting_Link",
            "meeting_link": "Meeting_Link",
            "meeting link": "Meeting_Link",
            "meet link": "Meeting_Link",
            "submission_link": "Submission_Link",
            "submission link": "Submission_Link",
            "task_status": "Submission_Status",
            "task status": "Submission_Status",
            "submission_status": "Submission_Status",
            "submission status": "Submission_Status",
            "review_status": "Verification_Status",
            "review status": "Verification_Status",
            "verification_status": "Verification_Status",
            "verification status": "Verification_Status",
            "reviewer_feedback": "Mentor_Feedback",
            "reviewer feedback": "Mentor_Feedback",
            "mentor_feedback": "Mentor_Feedback",
            "mentor feedback": "Mentor_Feedback",
            "feedback": "Mentor_Feedback",
            "next_follow_up_date": "Next_Review_Date",
            "next follow-up date": "Next_Review_Date",
            "next follow up date": "Next_Review_Date",
            "next_review_date": "Next_Review_Date",
            "next review date": "Next_Review_Date",
            "next_review_time": "Next_Review_Time",
            "next review time": "Next_Review_Time",
            "next_meeting_link": "Next_Meeting_Link",
            "next meeting link": "Next_Meeting_Link",
            "last_email_status": "Last_Email_Status",
            "last email status": "Last_Email_Status",
            "notes": "Notes",
            "remarks": "Notes",
        }

        # Rename existing columns
        new_cols = {}
        for c in df.columns:
            clean_c = str(c).strip()
            lower_c = clean_c.lower().replace("_", " ")
            clean_c_snake = clean_c.lower().replace(" ", "_")
            if clean_c in EXCEL_COLUMNS:
                new_cols[c] = clean_c
            elif lower_c in mapping:
                new_cols[c] = mapping[lower_c]
            elif clean_c_snake in mapping:
                new_cols[c] = mapping[clean_c_snake]
            else:
                new_cols[c] = clean_c
        df = df.rename(columns=new_cols)

        # Ensure all columns exist for internal representation
        for c in EXCEL_COLUMNS:
            if c not in df.columns:
                df[c] = ""

        return df

    @staticmethod
    def parse_and_validate(file_content: bytes, filename: str) -> Tuple[bool, Optional[pd.DataFrame], List[Dict[str, Any]], Dict[str, Any]]:
        """Validate uploaded Excel or CSV file with intelligent column auto-mapping.

        Returns:
            (is_valid, dataframe, list_of_row_errors, summary_stats)
        """
        errors: List[Dict[str, Any]] = []

        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine="openpyxl")
        except Exception as e:
            return False, None, [{"row": 0, "column": "File", "error": f"Failed to parse file: {str(e)}"}], {}

        # Check for empty dataframe
        if len(df) == 0:
            return False, df, [{"row": 0, "column": "Data", "error": "The uploaded workbook has no data rows."}], {}

        # Intelligently map column aliases
        raw_cols = [str(c).strip() for c in df.columns]
        df = ExcelService.normalize_uploaded_dataframe(df)

        # Check mandatory core columns
        mandatory_core = ["Intern_ID", "Intern_Name", "Email", "Department", "Task_ID", "Task_Title"]
        missing_mandatory = [c for c in mandatory_core if c not in raw_cols and c not in df.columns]
        # Check if they were present before default empty fill
        missing_from_upload = []
        for c in mandatory_core:
            if df[c].isna().all() or (df[c].astype(str).str.strip() == "").all():
                missing_from_upload.append(c)
        if missing_from_upload:
            return False, df, [{"row": 1, "column": "Header", "error": f"Missing mandatory columns: {', '.join(missing_from_upload)}"}], {}

        # 3. Row-by-row validation
        seen_intern_ids: Dict[str, int] = {}
        valid_rows_count = 0

        for idx, row in df.iterrows():
            row_num = idx + 2  # 1-indexed header + data
            row_has_error = False

            # Intern_ID
            intern_id = str(row.get("Intern_ID", "")).strip()
            if not intern_id or pd.isna(row.get("Intern_ID")):
                errors.append({"row": row_num, "column": "Intern_ID", "error": "Intern_ID is required and cannot be empty."})
                row_has_error = True

            # Intern_Name
            name = str(row.get("Intern_Name", "")).strip()
            if not name or pd.isna(row.get("Intern_Name")):
                errors.append({"row": row_num, "column": "Intern_Name", "error": "Intern_Name cannot be empty."})
                row_has_error = True

            # Email
            email = str(row.get("Email", "")).strip()
            if not validate_email_format(email):
                errors.append({"row": row_num, "column": "Email", "error": f"Invalid email format: '{email}'"})
                row_has_error = True

            # Mentor Email (optional, but if provided must be valid email)
            mentor_email = str(row.get("Mentor_Email", "")).strip()
            if mentor_email and mentor_email.lower() != "nan" and not validate_email_format(mentor_email):
                errors.append({"row": row_num, "column": "Mentor_Email", "error": f"Invalid mentor email format: '{mentor_email}'"})
                row_has_error = True

            # Department
            dept = str(row.get("Department", "")).strip()
            if not dept or pd.isna(row.get("Department")):
                errors.append({"row": row_num, "column": "Department", "error": "Department cannot be empty."})
                row_has_error = True

            # Task_ID & Task_Title
            task_id = str(row.get("Task_ID", "")).strip()
            task_title = str(row.get("Task_Title", "")).strip()
            if not task_id or pd.isna(row.get("Task_ID")):
                errors.append({"row": row_num, "column": "Task_ID", "error": "Task_ID cannot be empty."})
                row_has_error = True
            if not task_title or pd.isna(row.get("Task_Title")):
                errors.append({"row": row_num, "column": "Task_Title", "error": "Task_Title cannot be empty."})
                row_has_error = True

            # Dates
            assigned_date_raw = row.get("Assigned_Date")
            if assigned_date_raw and not pd.isna(assigned_date_raw):
                parsed_a = parse_date_value(assigned_date_raw)
                if not parsed_a:
                    errors.append({"row": row_num, "column": "Assigned_Date", "error": f"Invalid date in Assigned_Date: '{assigned_date_raw}'"})
                    row_has_error = True

            deadline_raw = row.get("Deadline")
            if deadline_raw and not pd.isna(deadline_raw):
                parsed_d = parse_date_value(deadline_raw)
                if not parsed_d:
                    errors.append({"row": row_num, "column": "Deadline", "error": f"Invalid date in Deadline: '{deadline_raw}'"})
                    row_has_error = True

            # Meeting link check
            meeting_link = row.get("Meeting_Link")
            if meeting_link and not pd.isna(meeting_link) and not validate_url_format(meeting_link):
                errors.append({"row": row_num, "column": "Meeting_Link", "error": f"Malformed meeting URL: '{meeting_link}'"})
                row_has_error = True

            # Next meeting link check
            next_meeting = row.get("Next_Meeting_Link")
            if next_meeting and not pd.isna(next_meeting) and not validate_url_format(next_meeting):
                errors.append({"row": row_num, "column": "Next_Meeting_Link", "error": f"Malformed next meeting URL: '{next_meeting}'"})
                row_has_error = True

            if not row_has_error:
                valid_rows_count += 1

        summary = {
            "total_rows": len(df),
            "valid_rows": valid_rows_count,
            "error_rows": len(set(e["row"] for e in errors)),
            "error_count": len(errors),
            "unique_interns": df["Intern_ID"].nunique() if "Intern_ID" in df.columns else 0,
            "unique_tasks": df["Task_ID"].nunique() if "Task_ID" in df.columns else 0,
        }

        is_valid = len(errors) == 0
        return is_valid, df, errors, summary

    @staticmethod
    def import_to_database(df: pd.DataFrame, db: Session, user_email: str = "coordinator@internflow.ai") -> Dict[str, int]:
        """Safely upsert records from validated DataFrame into the database."""
        interns_upserted = 0
        tasks_upserted = 0
        assignments_upserted = 0

        for _, row in df.iterrows():
            intern_id = str(row.get("Intern_ID", "")).strip()
            name = str(row.get("Intern_Name", "")).strip()
            email = str(row.get("Email", "")).strip()
            dept = str(row.get("Department", "")).strip()
            mentor_email = str(row.get("Mentor_Email", "")).strip() if pd.notna(row.get("Mentor_Email")) else None
            if mentor_email and mentor_email.lower() == "nan":
                mentor_email = None

            # Upsert Intern
            InternRepository.upsert(
                db=db,
                intern_id=intern_id,
                name=name,
                email=email,
                department=dept,
                mentor_email=mentor_email,
            )
            interns_upserted += 1

            # Task info
            task_id = str(row.get("Task_ID", "")).strip()
            task_title = str(row.get("Task_Title", "")).strip()
            task_desc = str(row.get("Task_Description", "")).strip() if pd.notna(row.get("Task_Description")) else task_title
            priority = str(row.get("Task_Priority", "Medium")).strip()
            if priority not in ("Low", "Medium", "High", "Urgent"):
                priority = "Medium"

            assigned_date = parse_date_value(row.get("Assigned_Date"))
            deadline = parse_date_value(row.get("Deadline"))
            req_docs = str(row.get("Required_Documents", "")).strip() if pd.notna(row.get("Required_Documents")) else None
            sub_instructions = str(row.get("Submission_Instructions", "")).strip() if pd.notna(row.get("Submission_Instructions")) else None

            TaskRepository.create_or_update(
                db=db,
                task_id=task_id,
                title=task_title,
                description=task_desc,
                priority=priority,
                assigned_date=assigned_date,
                deadline=deadline,
                required_documents=req_docs,
                submission_instructions=sub_instructions,
            )
            tasks_upserted += 1

            # Assignment info
            sub_status = str(row.get("Submission_Status", "Not Submitted")).strip()
            verif_status = str(row.get("Verification_Status", "Pending")).strip()
            mentor_feedback = str(row.get("Mentor_Feedback", "")).strip() if pd.notna(row.get("Mentor_Feedback")) else None
            meeting_link = str(row.get("Meeting_Link", "")).strip() if pd.notna(row.get("Meeting_Link")) else None
            sub_link = str(row.get("Submission_Link", "")).strip() if pd.notna(row.get("Submission_Link")) else None
            review_date = parse_date_value(row.get("Review_Date"))
            review_time = str(row.get("Review_Time", "")).strip() if pd.notna(row.get("Review_Time")) else None

            next_review_date = parse_date_value(row.get("Next_Review_Date"))
            next_review_time = str(row.get("Next_Review_Time", "")).strip() if pd.notna(row.get("Next_Review_Time")) else None
            next_meeting = str(row.get("Next_Meeting_Link", "")).strip() if pd.notna(row.get("Next_Meeting_Link")) else None
            last_email = str(row.get("Last_Email_Status", "None")).strip() if pd.notna(row.get("Last_Email_Status")) else "None"

            AssignmentRepository.upsert_assignment(
                db=db,
                intern_id=intern_id,
                task_id=task_id,
                mentor_email=mentor_email,
                assigned_date=assigned_date,
                deadline=deadline,
                submission_status=sub_status,
                verification_status=verif_status,
                mentor_feedback=mentor_feedback,
                review_date=review_date,
                review_time=review_time,
                meeting_link=meeting_link,
                submission_link=sub_link,
                next_review_date=next_review_date,
                next_review_time=next_review_time,
                next_meeting_link=next_meeting,
                last_email_status=last_email,
            )
            assignments_upserted += 1

        db.commit()

        # Audit log
        AuditRepository.log(
            db=db,
            user_email=user_email,
            role="admin",
            action="EXCEL_IMPORT",
            target_type="bulk",
            details={
                "interns_count": interns_upserted,
                "tasks_count": tasks_upserted,
                "assignments_count": assignments_upserted,
            },
        )
        db.commit()

        return {
            "interns_upserted": interns_upserted,
            "tasks_upserted": tasks_upserted,
            "assignments_upserted": assignments_upserted,
        }

    @staticmethod
    def export_from_database(db: Session, department: Optional[str] = None, mentor_email: Optional[str] = None, status: Optional[str] = None) -> bytes:
        """Export current database records into a fully styled 24-column Excel workbook."""
        assignments = AssignmentRepository.get_all(db=db, department=department, mentor_email=mentor_email, status=status)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "InternFlow_Master_Export"

        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        for col_idx, col_name in enumerate(EXCEL_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col_idx)].width = max(len(col_name) + 5, 18)

        for idx, a in enumerate(assignments, start=2):
            intern = a.intern
            task = a.task

            row_data = [
                a.intern_id,
                intern.name if intern else "",
                intern.email if intern else "",
                intern.department if intern else "",
                a.mentor_email or "",
                a.task_id,
                task.title if task else "",
                task.description if task else "",
                task.priority if task else "Medium",
                a.assigned_date.strftime("%Y-%m-%d") if a.assigned_date else "",
                a.deadline.strftime("%Y-%m-%d") if a.deadline else "",
                task.required_documents if task else "",
                task.submission_instructions if task else "",
                a.review_date.strftime("%Y-%m-%d") if a.review_date else "",
                a.review_time or "",
                a.meeting_link or "",
                a.submission_link or "",
                a.submission_status or "Not Submitted",
                a.verification_status or "Pending",
                a.mentor_feedback or "",
                a.next_review_date.strftime("%Y-%m-%d") if a.next_review_date else "",
                a.next_review_time or "",
                a.next_meeting_link or "",
                a.last_email_status or "None",
            ]

            for col_idx, val in enumerate(row_data, start=1):
                cell = ws.cell(row=idx, column=col_idx, value=val)
                cell.border = thin_border
                cell.font = Font(name="Arial", size=10)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

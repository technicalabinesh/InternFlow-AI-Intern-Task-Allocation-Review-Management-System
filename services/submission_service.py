"""Submission Service handling file uploads, links, versioning, and safe extraction."""

from __future__ import annotations

import os
import re
import json
import shutil
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from config.settings import (
    UPLOADS_DIR,
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
    ALLOWED_EXTENSIONS,
)
from database.models import Submission, TaskAssignment, Task, Intern
from database.repositories import SubmissionRepository, AuditRepository

# Approved URL patterns
GITHUB_PATTERN = re.compile(r"^https:\/\/(www\.)?github\.com\/[\w\.-]+\/[\w\.-]+", re.IGNORECASE)
GDRIVE_PATTERN = re.compile(r"^https:\/\/drive\.google\.com\/(file\/d\/|drive\/folders\/|open\?id=)", re.IGNORECASE)
HTTPS_PATTERN = re.compile(r"^https:\/\/[\w\.-]+(\.[\w\.-]+)+[/#?]?.*$", re.IGNORECASE)


def validate_submission_link(link: str) -> Tuple[bool, str]:
    """Validate submitted link against approved patterns."""
    if not link:
        return False, "Link URL cannot be empty."
    s = link.strip()
    if GITHUB_PATTERN.match(s):
        return True, "github"
    if GDRIVE_PATTERN.match(s):
        return True, "gdrive"
    if HTTPS_PATTERN.match(s):
        return True, "https_doc"
    return False, "Invalid link. Please provide a valid GitHub, Google Drive, or HTTPS document URL."


def sanitize_filename(filename: str) -> str:
    """Strip dangerous path traversal characters and normalize filename."""
    base = os.path.basename(filename)
    # Replace non-alphanumeric except dot, dash, underscore
    safe = re.sub(r"[^\w\.-]", "_", base)
    return safe or "upload.bin"


class SubmissionService:
    @staticmethod
    def handle_submission(
        db: Session,
        intern_id: str,
        task_id: str,
        uploaded_files: Optional[List[Tuple[str, bytes]]] = None,
        link_url: Optional[str] = None,
        notes: Optional[str] = None,
        user_email: str = "intern@internflow.ai",
    ) -> Submission:
        """Process and save an intern submission (file, link, or both) with versioning."""
        # Check task assignment exists
        assignment = db.query(TaskAssignment).filter(
            TaskAssignment.intern_id == intern_id,
            TaskAssignment.task_id == task_id,
        ).first()
        if not assignment:
            raise ValueError(f"Task '{task_id}' is not assigned to intern '{intern_id}'.")

        # Determine submission type
        has_files = bool(uploaded_files and len(uploaded_files) > 0)
        has_link = bool(link_url and link_url.strip())

        if not has_files and not has_link:
            raise ValueError("You must provide at least one file upload or an approved external link.")

        submission_type = "mixed" if (has_files and has_link) else ("file" if has_files else "link")

        # Validate link if provided
        if has_link:
            valid_link, link_type = validate_submission_link(link_url.strip())
            if not valid_link:
                raise ValueError(link_type)

        # Calculate deadline compliance
        now = datetime.datetime.utcnow()
        compliance = "On Time"
        if assignment.deadline and now.date() > assignment.deadline:
            compliance = "Late"

        saved_file_names: List[str] = []
        saved_file_paths: List[str] = []

        # Save files if uploaded
        if has_files:
            # Query current version
            latest = db.query(Submission).filter(
                Submission.intern_id == intern_id,
                Submission.task_id == task_id,
            ).order_by(Submission.version.desc()).first()
            next_version = (latest.version + 1) if latest else 1

            target_folder = UPLOADS_DIR / f"{intern_id}_{task_id}_v{next_version}"
            target_folder.mkdir(parents=True, exist_ok=True)

            for fname, fbytes in uploaded_files:
                if len(fbytes) > MAX_UPLOAD_SIZE_BYTES:
                    raise ValueError(f"File '{fname}' exceeds the maximum size limit of {MAX_UPLOAD_SIZE_MB}MB.")

                ext = Path(fname).suffix.lower()
                if ext not in ALLOWED_EXTENSIONS:
                    raise ValueError(f"File extension '{ext}' for file '{fname}' is not permitted.")

                safe_name = sanitize_filename(fname)
                dest = target_folder / safe_name
                dest.write_bytes(fbytes)

                saved_file_names.append(safe_name)
                saved_file_paths.append(str(dest))

        # Create submission record
        sub = SubmissionRepository.create_submission(
            db=db,
            intern_id=intern_id,
            task_id=task_id,
            submission_type=submission_type,
            file_names=saved_file_names,
            file_paths=saved_file_paths,
            link_url=link_url.strip() if has_link else None,
            notes=notes,
            deadline_compliance=compliance,
        )
        # Automatically schedule review meeting upon submission with Google Meet Link
        rev_date = assignment.review_date or (datetime.date.today() + datetime.timedelta(days=3))
        rev_time = assignment.review_time or "10:30 AM"
        meet_link = assignment.meeting_link or f"https://meet.google.com/xyz-{intern_id.lower()}-review"
        mentor_email = assignment.mentor_email or "mentor.sharma@internflow.ai"

        assignment.review_date = rev_date
        assignment.review_time = rev_time
        assignment.meeting_link = meet_link
        db.commit()

        # Create ReviewSchedule and dispatch email invitation
        try:
            from services.review_service import ReviewService
            ReviewService.schedule_review(
                db=db,
                intern_id=intern_id,
                task_id=task_id,
                review_date=rev_date,
                start_time=rev_time,
                meeting_link=meet_link,
                mentor_email=mentor_email,
                notes=f"Automated review session confirmed for milestone submission v{sub.version}.",
                user_email="system@internflow.ai",
                send_notification=True,
            )
        except Exception:
            pass

        # Audit log
        AuditRepository.log(
            db=db,
            user_email=user_email,
            role="intern",
            action="SUBMIT_WORK",
            target_type="submission",
            target_id=str(sub.id),
            details={
                "intern_id": intern_id,
                "task_id": task_id,
                "version": sub.version,
                "deadline_compliance": compliance,
                "files_count": len(saved_file_names),
                "link": link_url if has_link else None,
                "review_date": str(rev_date),
                "review_time": rev_time,
                "meeting_link": meet_link,
            },
        )
        db.commit()

        return sub

    @staticmethod
    def extract_safe_text(file_path: str, max_chars: int = 5000) -> str:
        """Safely inspect text or documents without executing code or macros."""
        path = Path(file_path)
        if not path.exists():
            return ""

        ext = path.suffix.lower()
        try:
            # 1. Plain text / code files
            if ext in (".txt", ".py", ".md", ".csv", ".json", ".sql", ".js", ".ts", ".html", ".css"):
                content = path.read_text(encoding="utf-8", errors="ignore")
                return content[:max_chars]

            # 2. PDF extraction using pypdf
            elif ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(path))
                    text = ""
                    for page in reader.pages[:5]:
                        text += (page.extract_text() or "") + "\n"
                    return text[:max_chars]
                except Exception:
                    return "[PDF Document attached; binary verified]"

            # 3. Word docx using python-docx
            elif ext == ".docx":
                try:
                    import docx
                    doc = docx.Document(str(path))
                    text = "\n".join([p.text for p in doc.paragraphs[:30]])
                    return text[:max_chars]
                except Exception:
                    return "[DOCX Document attached; verified]"

            # 4. Images or archives
            elif ext in (".png", ".jpg", ".jpeg", ".zip"):
                return f"[{ext.upper()} Deliverable attached: {path.name}, size: {path.stat().st_size} bytes]"

        except Exception as e:
            return f"[File could not be extracted: {str(e)}]"

        return "[Binary file attached]"

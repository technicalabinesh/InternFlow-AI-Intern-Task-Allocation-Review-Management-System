"""Verification Service coordinating safe file extraction and AI verification."""

from __future__ import annotations

import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from database.models import Submission, Task, VerificationReport, TaskAssignment
from services.submission_service import SubmissionService
from services.ai_service import AIService
from database.repositories import AuditRepository


class VerificationService:
    @staticmethod
    def run_verification(
        db: Session,
        submission_id: int,
        language: str = "en",
        user_email: str = "system@internflow.ai",
    ) -> VerificationReport:
        """Execute automated evidence-based verification on a submission."""
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise ValueError(f"Submission with ID {submission_id} not found.")

        task = db.query(Task).filter(Task.task_id == submission.task_id).first()
        if not task:
            raise ValueError(f"Task with ID {submission.task_id} not found.")

        # Extract text safely from uploaded files without executing anything
        parsed_contents: Dict[str, str] = {}
        if submission.file_paths:
            try:
                paths = json.loads(submission.file_paths)
                for p in paths:
                    parsed_contents[p] = SubmissionService.extract_safe_text(p)
            except Exception:
                pass

        # Generate structured verification report via AI engine
        report = AIService.generate_verification_report(
            task=task,
            submission=submission,
            parsed_file_contents=parsed_contents,
            language=language,
            db=db,
        )

        # Update assignment verification status
        assignment = db.query(TaskAssignment).filter(
            TaskAssignment.intern_id == submission.intern_id,
            TaskAssignment.task_id == submission.task_id,
        ).first()
        if assignment:
            assignment.verification_status = report.suggested_status
            db.commit()

        # Audit log
        AuditRepository.log(
            db=db,
            user_email=user_email,
            role="system",
            action="VERIFY_SUBMISSION",
            target_type="verification_report",
            target_id=str(report.id),
            details={
                "submission_id": submission.id,
                "completeness_pct": report.completeness_pct,
                "suggested_status": report.suggested_status,
            },
        )
        db.commit()

        return report

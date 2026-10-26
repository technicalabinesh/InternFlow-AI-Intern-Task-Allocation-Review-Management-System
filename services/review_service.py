"""Review service managing scheduling, calendar, outcomes, and follow-ups."""

from __future__ import annotations

import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from database.models import ReviewSchedule, TaskAssignment, Intern, Task
from database.repositories import ReviewRepository, AuditRepository
from services.email_service import EmailService


class ReviewService:
    @staticmethod
    def schedule_review(
        db: Session,
        intern_id: str,
        task_id: str,
        review_date: datetime.date,
        start_time: str,
        meeting_link: str,
        mentor_email: str,
        timezone: str = "Asia/Kolkata",
        end_time: Optional[str] = None,
        notes: Optional[str] = None,
        user_email: str = "coordinator@internflow.ai",
        send_notification: bool = True,
    ) -> ReviewSchedule:
        """Schedule a new review session and optionally notify the intern."""
        review = ReviewRepository.schedule(
            db=db,
            intern_id=intern_id,
            task_id=task_id,
            review_date=review_date,
            start_time=start_time,
            meeting_link=meeting_link,
            mentor_email=mentor_email,
            timezone=timezone,
            end_time=end_time,
            notes=notes,
        )
        db.commit()

        # Audit log
        AuditRepository.log(
            db=db,
            user_email=user_email,
            role="mentor",
            action="SCHEDULE_REVIEW",
            target_type="review",
            target_id=str(review.id),
            details={
                "intern_id": intern_id,
                "task_id": task_id,
                "review_date": str(review_date),
                "start_time": start_time,
            },
        )
        db.commit()

        if send_notification:
            intern = db.query(Intern).filter(Intern.intern_id == intern_id).first()
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if intern and task:
                ctx = {
                    "Intern_Name": intern.name,
                    "Task_Title": task.title,
                    "Review_Date": review_date.strftime("%Y-%m-%d"),
                    "Review_Time": start_time,
                    "Timezone": timezone,
                    "Meeting_Link": meeting_link,
                    "Mentor_Email": mentor_email,
                }
                EmailService.send_email(
                    recipient_email=intern.email,
                    recipient_name=intern.name,
                    template_type="review_invitation",
                    context=ctx,
                    task_id=task_id,
                )

        return review

    @staticmethod
    def complete_review(
        db: Session,
        intern_id: str,
        task_id: str,
        review_id: Optional[int],
        outcome_status: str,  # Approved, Needs Changes, Rejected
        mentor_comments: str,
        next_review_date: Optional[datetime.date] = None,
        next_review_time: Optional[str] = None,
        next_meeting_link: Optional[str] = None,
        user_email: str = "mentor@internflow.ai",
        send_followup_email: bool = True,
    ) -> Tuple[TaskAssignment, Optional[str]]:
        """Complete a review meeting, record decision, and configure next review if needed."""
        assignment = db.query(TaskAssignment).filter(
            TaskAssignment.intern_id == intern_id,
            TaskAssignment.task_id == task_id,
        ).first()
        if not assignment:
            raise ValueError(f"Assignment for intern {intern_id} and task {task_id} not found.")

        # Update assignment state
        assignment.submission_status = outcome_status
        assignment.mentor_feedback = mentor_comments
        if next_review_date:
            assignment.next_review_date = next_review_date
            assignment.next_review_time = next_review_time
            assignment.next_meeting_link = next_meeting_link

        # Update Review record if specified
        if review_id:
            review = db.query(ReviewSchedule).filter(ReviewSchedule.id == review_id).first()
            if review:
                review.status = "Completed"
                review.decisions = outcome_status
                review.notes = mentor_comments
                if next_review_date:
                    review.follow_up_email_sent = send_followup_email

        db.commit()

        # Audit log
        AuditRepository.log(
            db=db,
            user_email=user_email,
            role="mentor",
            action="COMPLETE_REVIEW",
            target_type="assignment",
            target_id=f"{intern_id}:{task_id}",
            details={
                "outcome": outcome_status,
                "has_next_review": bool(next_review_date),
            },
        )
        db.commit()

        email_status_msg = None
        if send_followup_email:
            intern = assignment.intern
            task = assignment.task
            if intern and task:
                ctx = {
                    "Intern_Name": intern.name,
                    "Task_Title": task.title,
                    "Submission_Status": outcome_status,
                    "Verification_Status": assignment.verification_status,
                    "Mentor_Feedback": mentor_comments,
                    "Next_Review_Date": next_review_date.strftime("%Y-%m-%d") if next_review_date else "",
                    "Next_Review_Time": next_review_time or "",
                    "Next_Meeting_Link": next_meeting_link or "",
                }
                template_to_use = "task_approved" if outcome_status == "Approved" else "changes_requested"
                success, status_label, msg = EmailService.send_email(
                    recipient_email=intern.email,
                    recipient_name=intern.name,
                    template_type=template_to_use,
                    context=ctx,
                    task_id=task_id,
                )
                email_status_msg = f"Follow-up email status: {status_label} ({msg})"

        return assignment, email_status_msg

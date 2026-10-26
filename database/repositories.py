"""Repository functions for database operations in InternFlow AI."""

from __future__ import annotations

import datetime
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from database.models import (
    User,
    Intern,
    Task,
    TaskAssignment,
    TaskExplanation,
    Submission,
    VerificationReport,
    ReviewSchedule,
    EmailLog,
    AuditLog,
)


class InternRepository:
    @staticmethod
    def get_all(db: Session, department: Optional[str] = None, mentor_email: Optional[str] = None, search: Optional[str] = None) -> List[Intern]:
        query = db.query(Intern)
        if department and department != "All":
            query = query.filter(Intern.department == department)
        if mentor_email and mentor_email != "All":
            query = query.filter(Intern.mentor_email == mentor_email)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Intern.intern_id.ilike(search_term),
                    Intern.name.ilike(search_term),
                    Intern.email.ilike(search_term),
                )
            )
        return query.order_by(Intern.intern_id).all()

    @staticmethod
    def get_by_id(db: Session, intern_id: str) -> Optional[Intern]:
        return db.query(Intern).filter(Intern.intern_id == intern_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Intern]:
        return db.query(Intern).filter(Intern.email.ilike(email.strip())).first()

    @staticmethod
    def upsert(db: Session, intern_id: str, name: str, email: str, department: str, mentor_email: Optional[str] = None) -> Intern:
        intern = db.query(Intern).filter(Intern.intern_id == intern_id).first()
        if intern:
            intern.name = name
            intern.email = email
            intern.department = department
            if mentor_email:
                intern.mentor_email = mentor_email
        else:
            intern = Intern(
                intern_id=intern_id,
                name=name,
                email=email,
                department=department,
                mentor_email=mentor_email,
            )
            db.add(intern)
        db.flush()
        return intern


class TaskRepository:
    @staticmethod
    def get_all(db: Session, priority: Optional[str] = None, search: Optional[str] = None) -> List[Task]:
        query = db.query(Task)
        if priority and priority != "All":
            query = query.filter(Task.priority == priority)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Task.task_id.ilike(search_term),
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                )
            )
        return query.order_by(Task.task_id).all()

    @staticmethod
    def get_by_id(db: Session, task_id: str) -> Optional[Task]:
        return db.query(Task).filter(Task.task_id == task_id).first()

    @staticmethod
    def create_or_update(
        db: Session,
        task_id: str,
        title: str,
        description: str,
        priority: str = "Medium",
        assigned_date: Optional[datetime.date] = None,
        deadline: Optional[datetime.date] = None,
        required_documents: Optional[str] = None,
        submission_instructions: Optional[str] = None,
        acceptance_criteria: Optional[str] = None,
        tools_required: Optional[str] = None,
    ) -> Task:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.title = title
            task.description = description
            task.priority = priority
            if assigned_date:
                task.assigned_date = assigned_date
            if deadline:
                task.deadline = deadline
            if required_documents:
                task.required_documents = required_documents
            if submission_instructions:
                task.submission_instructions = submission_instructions
            if acceptance_criteria:
                task.acceptance_criteria = acceptance_criteria
            if tools_required:
                task.tools_required = tools_required
        else:
            task = Task(
                task_id=task_id,
                title=title,
                description=description,
                priority=priority,
                assigned_date=assigned_date or datetime.date.today(),
                deadline=deadline,
                required_documents=required_documents,
                submission_instructions=submission_instructions,
                acceptance_criteria=acceptance_criteria,
                tools_required=tools_required,
            )
            db.add(task)
        db.flush()
        return task


class AssignmentRepository:
    @staticmethod
    def get_all(
        db: Session,
        department: Optional[str] = None,
        mentor_email: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[TaskAssignment]:
        query = db.query(TaskAssignment).join(Intern, TaskAssignment.intern_id == Intern.intern_id).join(Task, TaskAssignment.task_id == Task.task_id)

        if department and department != "All":
            query = query.filter(Intern.department == department)
        if mentor_email and mentor_email != "All":
            query = query.filter(TaskAssignment.mentor_email == mentor_email)
        if status and status != "All":
            query = query.filter(TaskAssignment.submission_status == status)
        if priority and priority != "All":
            query = query.filter(Task.priority == priority)
        if search:
            st = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    TaskAssignment.intern_id.ilike(st),
                    Intern.name.ilike(st),
                    Task.title.ilike(st),
                    TaskAssignment.task_id.ilike(st),
                )
            )
        return query.order_by(TaskAssignment.deadline.asc().nullslast()).all()

    @staticmethod
    def get_by_intern_and_task(db: Session, intern_id: str, task_id: str) -> Optional[TaskAssignment]:
        return db.query(TaskAssignment).filter(
            TaskAssignment.intern_id == intern_id,
            TaskAssignment.task_id == task_id,
        ).first()

    @staticmethod
    def get_by_intern(db: Session, intern_id: str) -> List[TaskAssignment]:
        return db.query(TaskAssignment).filter(TaskAssignment.intern_id == intern_id).all()

    @staticmethod
    def get_by_mentor(db: Session, mentor_email: str) -> List[TaskAssignment]:
        return db.query(TaskAssignment).filter(TaskAssignment.mentor_email.ilike(mentor_email.strip())).all()

    @staticmethod
    def get_overdue(db: Session) -> List[TaskAssignment]:
        today = datetime.date.today()
        return db.query(TaskAssignment).filter(
            TaskAssignment.deadline < today,
            TaskAssignment.submission_status.in_(["Not Submitted", "Needs Changes"]),
        ).all()

    @staticmethod
    def upsert_assignment(
        db: Session,
        intern_id: str,
        task_id: str,
        mentor_email: Optional[str] = None,
        assigned_date: Optional[datetime.date] = None,
        deadline: Optional[datetime.date] = None,
        submission_status: str = "Not Submitted",
        verification_status: str = "Pending",
        mentor_feedback: Optional[str] = None,
        review_date: Optional[datetime.date] = None,
        review_time: Optional[str] = None,
        meeting_link: Optional[str] = None,
        submission_link: Optional[str] = None,
        next_review_date: Optional[datetime.date] = None,
        next_review_time: Optional[str] = None,
        next_meeting_link: Optional[str] = None,
        last_email_status: Optional[str] = None,
    ) -> TaskAssignment:
        assignment = db.query(TaskAssignment).filter(
            TaskAssignment.intern_id == intern_id,
            TaskAssignment.task_id == task_id,
        ).first()

        if assignment:
            if mentor_email:
                assignment.mentor_email = mentor_email
            if assigned_date:
                assignment.assigned_date = assigned_date
            if deadline:
                assignment.deadline = deadline
            if submission_status:
                assignment.submission_status = submission_status
            if verification_status:
                assignment.verification_status = verification_status
            if mentor_feedback:
                assignment.mentor_feedback = mentor_feedback
            if review_date:
                assignment.review_date = review_date
            if review_time:
                assignment.review_time = review_time
            if meeting_link:
                assignment.meeting_link = meeting_link
            if submission_link:
                assignment.submission_link = submission_link
            if next_review_date:
                assignment.next_review_date = next_review_date
            if next_review_time:
                assignment.next_review_time = next_review_time
            if next_meeting_link:
                assignment.next_meeting_link = next_meeting_link
            if last_email_status:
                assignment.last_email_status = last_email_status
        else:
            assignment = TaskAssignment(
                intern_id=intern_id,
                task_id=task_id,
                mentor_email=mentor_email,
                assigned_date=assigned_date or datetime.date.today(),
                deadline=deadline,
                submission_status=submission_status or "Not Submitted",
                verification_status=verification_status or "Pending",
                mentor_feedback=mentor_feedback,
                review_date=review_date,
                review_time=review_time,
                meeting_link=meeting_link,
                submission_link=submission_link,
                next_review_date=next_review_date,
                next_review_time=next_review_time,
                next_meeting_link=next_meeting_link,
                last_email_status=last_email_status or "None",
            )
            db.add(assignment)
        db.flush()
        return assignment


class SubmissionRepository:
    @staticmethod
    def create_submission(
        db: Session,
        intern_id: str,
        task_id: str,
        submission_type: str,
        file_names: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None,
        link_url: Optional[str] = None,
        notes: Optional[str] = None,
        deadline_compliance: str = "On Time",
    ) -> Submission:
        # Determine current version
        past_submissions = db.query(Submission).filter(
            Submission.intern_id == intern_id,
            Submission.task_id == task_id,
        ).order_by(Submission.version.desc()).all()

        next_version = 1
        if past_submissions:
            next_version = past_submissions[0].version + 1
            for ps in past_submissions:
                ps.is_active_version = False

        sub = Submission(
            intern_id=intern_id,
            task_id=task_id,
            version=next_version,
            submission_type=submission_type,
            file_names=json.dumps(file_names or []),
            file_paths=json.dumps(file_paths or []),
            link_url=link_url,
            notes=notes,
            submitted_at=datetime.datetime.utcnow(),
            deadline_compliance=deadline_compliance,
            verification_status="Submitted",
            is_active_version=True,
        )
        db.add(sub)
        db.flush()

        # Update assignment submission status
        assignment = db.query(TaskAssignment).filter(
            TaskAssignment.intern_id == intern_id,
            TaskAssignment.task_id == task_id,
        ).first()
        if assignment:
            assignment.submission_status = "Submitted" if next_version == 1 else "Resubmitted"
            if link_url:
                assignment.submission_link = link_url
            db.flush()

        return sub

    @staticmethod
    def get_latest(db: Session, intern_id: str, task_id: str) -> Optional[Submission]:
        return db.query(Submission).filter(
            Submission.intern_id == intern_id,
            Submission.task_id == task_id,
            Submission.is_active_version == True,
        ).order_by(Submission.version.desc()).first()

    @staticmethod
    def get_history(db: Session, intern_id: str, task_id: str) -> List[Submission]:
        return db.query(Submission).filter(
            Submission.intern_id == intern_id,
            Submission.task_id == task_id,
        ).order_by(Submission.version.desc()).all()


class ReviewRepository:
    @staticmethod
    def schedule(
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
    ) -> ReviewSchedule:
        review = ReviewSchedule(
            intern_id=intern_id,
            task_id=task_id,
            review_date=review_date,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            meeting_link=meeting_link,
            mentor_email=mentor_email,
            status="Scheduled",
            notes=notes,
        )
        db.add(review)
        db.flush()

        # Also update current review details in assignment
        assignment = db.query(TaskAssignment).filter(
            TaskAssignment.intern_id == intern_id,
            TaskAssignment.task_id == task_id,
        ).first()
        if assignment:
            assignment.review_date = review_date
            assignment.review_time = start_time
            assignment.meeting_link = meeting_link
            db.flush()

        return review

    @staticmethod
    def get_upcoming(db: Session, mentor_email: Optional[str] = None) -> List[ReviewSchedule]:
        today = datetime.date.today()
        query = db.query(ReviewSchedule).filter(
            ReviewSchedule.review_date >= today,
            ReviewSchedule.status == "Scheduled",
        )
        if mentor_email and mentor_email != "All":
            query = query.filter(ReviewSchedule.mentor_email.ilike(mentor_email.strip()))
        return query.order_by(ReviewSchedule.review_date.asc(), ReviewSchedule.start_time.asc()).all()


class AuditRepository:
    @staticmethod
    def log(
        db: Session,
        user_email: str,
        role: str,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_email=user_email,
            role=role,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            details=json.dumps(details or {}),
            timestamp=datetime.datetime.utcnow(),
        )
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def get_recent(db: Session, limit: int = 100) -> List[AuditLog]:
        return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

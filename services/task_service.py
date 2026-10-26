"""Task service handling creation, bulk allocation, and overdue tracking."""

from __future__ import annotations

import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from database.models import Task, TaskAssignment, Intern, AuditLog
from database.repositories import TaskRepository, AssignmentRepository, AuditRepository


class TaskService:
    @staticmethod
    def create_task(
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
        user_email: str = "admin@internflow.ai",
    ) -> Task:
        task = TaskRepository.create_or_update(
            db=db,
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            assigned_date=assigned_date,
            deadline=deadline,
            required_documents=required_documents,
            submission_instructions=submission_instructions,
            acceptance_criteria=acceptance_criteria,
            tools_required=tools_required,
        )
        db.commit()

        AuditRepository.log(
            db=db,
            user_email=user_email,
            role="admin",
            action="CREATE_TASK",
            target_type="task",
            target_id=task_id,
            details={"title": title, "priority": priority},
        )
        db.commit()
        return task

    @staticmethod
    def bulk_allocate_task(
        db: Session,
        intern_ids: List[str],
        task_id: str,
        mentor_email: Optional[str] = None,
        assigned_date: Optional[datetime.date] = None,
        deadline: Optional[datetime.date] = None,
        review_date: Optional[datetime.date] = None,
        review_time: Optional[str] = None,
        meeting_link: Optional[str] = None,
        user_email: str = "admin@internflow.ai",
    ) -> Dict[str, Any]:
        """Allocate a task to multiple interns with audit tracking."""
        task = TaskRepository.get_by_id(db=db, task_id=task_id)
        if not task:
            raise ValueError(f"Task with ID '{task_id}' does not exist.")

        assigned_count = 0
        assigned_list = []

        for intern_id in intern_ids:
            intern = db.query(Intern).filter(Intern.intern_id == intern_id).first()
            if not intern:
                continue

            chosen_mentor = mentor_email or intern.mentor_email
            assignment = AssignmentRepository.upsert_assignment(
                db=db,
                intern_id=intern_id,
                task_id=task_id,
                mentor_email=chosen_mentor,
                assigned_date=assigned_date or datetime.date.today(),
                deadline=deadline or task.deadline,
                submission_status="Not Submitted",
                verification_status="Pending",
                review_date=review_date,
                review_time=review_time,
                meeting_link=meeting_link,
            )
            assigned_count += 1
            assigned_list.append(intern_id)

        db.commit()

        AuditRepository.log(
            db=db,
            user_email=user_email,
            role="admin",
            action="BULK_ALLOCATE_TASK",
            target_type="task",
            target_id=task_id,
            details={"allocated_count": assigned_count, "intern_ids": assigned_list},
        )
        db.commit()

        return {
            "task_id": task_id,
            "allocated_count": assigned_count,
            "interns": assigned_list,
        }

    @staticmethod
    def get_overdue_tasks(db: Session) -> List[TaskAssignment]:
        """Detect and return all assignments that have passed their deadline."""
        return AssignmentRepository.get_overdue(db=db)

    @staticmethod
    def reassign_mentor(
        db: Session,
        intern_id: str,
        task_id: str,
        new_mentor_email: str,
        user_email: str = "admin@internflow.ai",
    ) -> TaskAssignment:
        assignment = AssignmentRepository.get_by_intern_and_task(db=db, intern_id=intern_id, task_id=task_id)
        if not assignment:
            raise ValueError(f"Assignment for intern {intern_id} and task {task_id} not found.")

        old_mentor = assignment.mentor_email
        assignment.mentor_email = new_mentor_email
        db.commit()

        AuditRepository.log(
            db=db,
            user_email=user_email,
            role="admin",
            action="REASSIGN_MENTOR",
            target_type="assignment",
            target_id=f"{intern_id}:{task_id}",
            details={"old_mentor": old_mentor, "new_mentor": new_mentor_email},
        )
        db.commit()
        return assignment

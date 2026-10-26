"""SQLAlchemy models for InternFlow AI.

Defines the database schema for users, interns, tasks, assignments,
explanations, submissions, verifications, reviews, emails, and audit logs.
"""

from __future__ import annotations

import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    Time,
    Boolean,
    Float,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from database.connection import Base


class User(Base):
    """User model for Role-Based Access Control."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="intern")  # admin, mentor, intern
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class Intern(Base):
    """Intern model tracking profile and metadata."""
    __tablename__ = "interns"

    id = Column(Integer, primary_key=True, index=True)
    intern_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False, index=True)
    mentor_email = Column(String(255), nullable=True, index=True)
    status = Column(String(50), default="Active", nullable=False)  # Active, Inactive, Completed
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    assignments = relationship("TaskAssignment", back_populates="intern", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="intern", cascade="all, delete-orphan")
    reviews = relationship("ReviewSchedule", back_populates="intern", cascade="all, delete-orphan")


class Task(Base):
    """Task catalog model holding core task definitions."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), default="Medium", nullable=False)  # Low, Medium, High, Urgent
    assigned_date = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)
    required_documents = Column(Text, nullable=True)
    submission_instructions = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    tools_required = Column(String(255), nullable=True)
    status = Column(String(50), default="Assigned", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    explanations = relationship("TaskExplanation", back_populates="task", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="task", cascade="all, delete-orphan")


class TaskAssignment(Base):
    """Mapping of an assigned task to an intern with real-time tracking."""
    __tablename__ = "task_assignments"

    id = Column(Integer, primary_key=True, index=True)
    intern_id = Column(String(100), ForeignKey("interns.intern_id"), nullable=False, index=True)
    task_id = Column(String(100), ForeignKey("tasks.task_id"), nullable=False, index=True)
    mentor_email = Column(String(255), nullable=True, index=True)
    assigned_date = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)

    # Status tracking (exact master prompt values)
    # Not Submitted, Submitted, Under Review, Needs Changes, Approved, Rejected, Resubmitted
    submission_status = Column(String(50), default="Not Submitted", nullable=False, index=True)
    verification_status = Column(String(50), default="Pending", nullable=False)
    mentor_feedback = Column(Text, nullable=True)

    # Current Review schedule
    review_date = Column(Date, nullable=True)
    review_time = Column(String(50), nullable=True)
    meeting_link = Column(String(500), nullable=True)
    submission_link = Column(String(500), nullable=True)

    # Next Review schedule
    next_review_date = Column(Date, nullable=True)
    next_review_time = Column(String(50), nullable=True)
    next_meeting_link = Column(String(500), nullable=True)

    # Last communication
    last_email_status = Column(String(100), default="None", nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    intern = relationship("Intern", back_populates="assignments")
    task = relationship("Task", back_populates="assignments")

    __table_args__ = (
        Index("idx_intern_task", "intern_id", "task_id"),
    )


class TaskExplanation(Base):
    """AI-Generated simplified explanation for an assigned task."""
    __tablename__ = "task_explanations"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), ForeignKey("tasks.task_id"), nullable=False, index=True)
    language = Column(String(10), default="en", nullable=False)  # en, ta

    # 10 core questions
    summary = Column(Text, nullable=True)
    what_is_this_task = Column(Text, nullable=True)
    why_doing_it = Column(Text, nullable=True)
    what_must_do = Column(Text, nullable=True)
    step_by_step = Column(Text, nullable=True)
    tools_required = Column(Text, nullable=True)
    deliverables = Column(Text, nullable=True)
    final_output_look = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    deadline_info = Column(Text, nullable=True)
    common_mistakes = Column(Text, nullable=True)

    incomplete_flags = Column(Text, nullable=True)  # Warnings if original task lacks details
    full_explanation_text = Column(Text, nullable=False)
    is_cached = Column(Boolean, default=True)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    task = relationship("Task", back_populates="explanations")


class Submission(Base):
    """Intern work submission supporting files and approved links."""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    intern_id = Column(String(100), ForeignKey("interns.intern_id"), nullable=False, index=True)
    task_id = Column(String(100), ForeignKey("tasks.task_id"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    submission_type = Column(String(50), default="file", nullable=False)  # file, link, mixed

    file_names = Column(Text, nullable=True)   # JSON string list of filenames
    file_paths = Column(Text, nullable=True)   # JSON string list of storage paths
    link_url = Column(String(1000), nullable=True)
    notes = Column(Text, nullable=True)

    submitted_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    deadline_compliance = Column(String(50), default="On Time", nullable=False)  # On Time, Late
    verification_status = Column(String(50), default="Submitted", nullable=False)
    reviewer_comments = Column(Text, nullable=True)
    is_active_version = Column(Boolean, default=True)

    # Relationships
    intern = relationship("Intern", back_populates="submissions")
    task = relationship("Task", back_populates="submissions")
    verification_reports = relationship("VerificationReport", back_populates="submission", cascade="all, delete-orphan")


class VerificationReport(Base):
    """Structured AI Verification Report for an intern submission."""
    __tablename__ = "verification_reports"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, index=True)
    intern_id = Column(String(100), nullable=False, index=True)
    task_id = Column(String(100), nullable=False, index=True)

    completeness_pct = Column(Float, default=0.0, nullable=False)
    requirement_results = Column(Text, nullable=False)  # JSON with each requirement satisfied/partial/missing
    evidence_found = Column(Text, nullable=False)       # JSON or structured evidence
    missing_requirements = Column(Text, nullable=True)  # JSON or list of missing deliverables
    potential_concerns = Column(Text, nullable=True)
    improvement_suggestions = Column(Text, nullable=False)  # JSON list of actionable items
    good_points = Column(Text, nullable=True)              # JSON list of strengths/good items
    not_good_points = Column(Text, nullable=True)          # JSON list of deficiencies/not good items
    recommended_next_actions = Column(Text, nullable=False)
    suggested_status = Column(String(50), nullable=False)   # Needs Changes, Approved, Rejected, etc.

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    submission = relationship("Submission", back_populates="verification_reports")


class ReviewSchedule(Base):
    """Scheduled review meeting records."""
    __tablename__ = "review_schedules"

    id = Column(Integer, primary_key=True, index=True)
    intern_id = Column(String(100), ForeignKey("interns.intern_id"), nullable=False, index=True)
    task_id = Column(String(100), ForeignKey("tasks.task_id"), nullable=False, index=True)

    review_date = Column(Date, nullable=False)
    start_time = Column(String(50), nullable=False)
    end_time = Column(String(50), nullable=True)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    meeting_link = Column(String(500), nullable=False)
    mentor_email = Column(String(255), nullable=False)

    status = Column(String(50), default="Scheduled", nullable=False)  # Scheduled, Completed, Cancelled, Rescheduled
    notes = Column(Text, nullable=True)
    decisions = Column(Text, nullable=True)
    follow_up_email_sent = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    intern = relationship("Intern", back_populates="reviews")


class EmailLog(Base):
    """Audit log for automated and manual emails."""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255), nullable=True)
    template_type = Column(String(100), nullable=False)
    subject = Column(String(500), nullable=False)
    body_preview = Column(Text, nullable=True)
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)

    status = Column(String(50), default="Pending", nullable=False)  # Sent, Simulated, Failed, Pending
    provider = Column(String(50), default="mock", nullable=False)
    message_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class AuditLog(Base):
    """System-wide audit trail for actions, updates, and allocations."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., 'ALLOCATE_TASK', 'SUBMIT_WORK', 'SCHEDULE_REVIEW'
    target_type = Column(String(100), nullable=True)  # e.g., 'intern', 'task', 'submission'
    target_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

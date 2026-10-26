"""Tests for Review Scheduling and Follow-Up Management."""

import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Intern, Task, TaskAssignment, ReviewSchedule
from database.repositories import InternRepository
from services.task_service import TaskService
from services.review_service import ReviewService


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_schedule_review_preserves_details(test_db):
    InternRepository.upsert(
        db=test_db,
        intern_id="INT-REV-1",
        name="Reviewee Intern",
        email="rev1@test.com",
        department="Data Science",
        mentor_email="mentor.ds@test.com",
    )
    TaskService.create_task(
        db=test_db,
        task_id="TSK-REV-1",
        title="ML Review Task",
        description="Review model accuracy",
    )
    TaskService.bulk_allocate_task(test_db, ["INT-REV-1"], "TSK-REV-1")

    rev_date = datetime.date.today() + datetime.timedelta(days=3)
    meeting_link = "https://meet.google.com/abc-defg-hij"

    review = ReviewService.schedule_review(
        db=test_db,
        intern_id="INT-REV-1",
        task_id="TSK-REV-1",
        review_date=rev_date,
        start_time="11:30 AM",
        meeting_link=meeting_link,
        mentor_email="mentor.ds@test.com",
        timezone="Asia/Kolkata",
        send_notification=False,
    )

    assert review.id is not None
    assert review.review_date == rev_date
    assert review.start_time == "11:30 AM"
    assert review.timezone == "Asia/Kolkata"
    assert review.meeting_link == meeting_link
    assert review.status == "Scheduled"

    # Also check assignment updated
    assignment = test_db.query(TaskAssignment).filter(
        TaskAssignment.intern_id == "INT-REV-1",
        TaskAssignment.task_id == "TSK-REV-1",
    ).first()
    assert assignment.review_date == rev_date
    assert assignment.review_time == "11:30 AM"


def test_complete_review_and_schedule_followup(test_db):
    InternRepository.upsert(
        db=test_db,
        intern_id="INT-REV-2",
        name="Followup Intern",
        email="rev2@test.com",
        department="Engineering",
        mentor_email="mentor.eng@test.com",
    )
    TaskService.create_task(
        db=test_db,
        task_id="TSK-REV-2",
        title="Followup Task",
        description="Requires follow-up review",
    )
    TaskService.bulk_allocate_task(test_db, ["INT-REV-2"], "TSK-REV-2")

    review = ReviewService.schedule_review(
        db=test_db,
        intern_id="INT-REV-2",
        task_id="TSK-REV-2",
        review_date=datetime.date.today(),
        start_time="10:00 AM",
        meeting_link="https://meet.google.com/first-link",
        mentor_email="mentor.eng@test.com",
        send_notification=False,
    )

    next_date = datetime.date.today() + datetime.timedelta(days=7)
    assignment, _ = ReviewService.complete_review(
        db=test_db,
        intern_id="INT-REV-2",
        task_id="TSK-REV-2",
        review_id=review.id,
        outcome_status="Needs Changes",
        mentor_comments="Fix bug in calculation and resubmit.",
        next_review_date=next_date,
        next_review_time="03:00 PM",
        next_meeting_link="https://meet.google.com/next-link",
        send_followup_email=False,
    )

    assert assignment.submission_status == "Needs Changes"
    assert assignment.mentor_feedback == "Fix bug in calculation and resubmit."
    assert assignment.next_review_date == next_date
    assert assignment.next_review_time == "03:00 PM"
    assert assignment.next_meeting_link == "https://meet.google.com/next-link"

    # Review status should be completed
    test_db.refresh(review)
    assert review.status == "Completed"

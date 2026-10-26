"""Tests for Task Creation, Bulk Allocation, Overdue Tracking, and Reassignment."""

import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Intern, Task, TaskAssignment, AuditLog
from database.repositories import InternRepository
from services.task_service import TaskService


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


def test_task_creation_and_bulk_allocation(test_db):
    # Create 3 interns
    for i in range(1, 4):
        InternRepository.upsert(
            db=test_db,
            intern_id=f"INT-TEST-{i}",
            name=f"Intern {i}",
            email=f"intern{i}@test.com",
            department="Engineering",
            mentor_email="mentor@test.com",
        )
    test_db.commit()

    # Create task
    task = TaskService.create_task(
        db=test_db,
        task_id="TSK-UNIT-01",
        title="Unit Test Task",
        description="Verify task allocation pipeline",
        priority="High",
        deadline=datetime.date.today() + datetime.timedelta(days=5),
        required_documents="code.py, test.py",
        submission_instructions="Submit via Git",
    )
    assert task.task_id == "TSK-UNIT-01"

    # Bulk allocate to 3 interns
    alloc_result = TaskService.bulk_allocate_task(
        db=test_db,
        intern_ids=["INT-TEST-1", "INT-TEST-2", "INT-TEST-3"],
        task_id="TSK-UNIT-01",
        mentor_email="lead.mentor@test.com",
    )
    assert alloc_result["allocated_count"] == 3

    assignments = test_db.query(TaskAssignment).filter(TaskAssignment.task_id == "TSK-UNIT-01").all()
    assert len(assignments) == 3
    for a in assignments:
        assert a.mentor_email == "lead.mentor@test.com"
        assert a.submission_status == "Not Submitted"


def test_overdue_task_detection(test_db):
    InternRepository.upsert(
        db=test_db,
        intern_id="INT-OVERDUE",
        name="Late Intern",
        email="late@test.com",
        department="Engineering",
    )
    task = TaskService.create_task(
        db=test_db,
        task_id="TSK-OVERDUE",
        title="Past Due Task",
        description="Task past deadline",
        deadline=datetime.date.today() - datetime.timedelta(days=2),
    )
    TaskService.bulk_allocate_task(
        db=test_db,
        intern_ids=["INT-OVERDUE"],
        task_id="TSK-OVERDUE",
    )

    overdue = TaskService.get_overdue_tasks(test_db)
    assert len(overdue) >= 1
    assert any(o.task_id == "TSK-OVERDUE" for o in overdue)


def test_mentor_reassignment_with_audit(test_db):
    InternRepository.upsert(
        db=test_db,
        intern_id="INT-REASSIGN",
        name="Reassign Intern",
        email="reassign@test.com",
        department="Engineering",
    )
    TaskService.create_task(
        db=test_db,
        task_id="TSK-REASSIGN",
        title="Reassignment Task",
        description="Test reassigning mentor",
    )
    TaskService.bulk_allocate_task(
        db=test_db,
        intern_ids=["INT-REASSIGN"],
        task_id="TSK-REASSIGN",
        mentor_email="original.mentor@test.com",
    )

    updated = TaskService.reassign_mentor(
        db=test_db,
        intern_id="INT-REASSIGN",
        task_id="TSK-REASSIGN",
        new_mentor_email="new.mentor@test.com",
    )
    assert updated.mentor_email == "new.mentor@test.com"

    # Audit log check
    audit = test_db.query(AuditLog).filter(AuditLog.action == "REASSIGN_MENTOR").first()
    assert audit is not None
    assert "new.mentor@test.com" in audit.details

"""Tests for Voice Narration, Google Gemini AI, and What is Good vs Not Good Comparison."""

import pytest
from database.models import Base, Intern, Task, Submission
from database.repositories import InternRepository
from services.task_service import TaskService
from services.submission_service import SubmissionService
from services.verification_service import VerificationService
from services.voice_service import VoiceService
from services.ai_service import GeminiAIProvider, MockAIProvider
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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


def test_voice_task_briefing_generation():
    audio_bytes, path = VoiceService.generate_task_briefing_audio(
        task_id="TSK-TEST-VOICE",
        task_title="Build Full Stack Dashboard",
        what_must_do="Develop an interactive analytics portal with Plotly and Streamlit.",
        step_by_step="1. Clone repo. 2. Write Python script. 3. Run unit tests.",
        deliverables="dashboard.py, README.md",
        deadline_info="Due next Friday",
        language="en",
    )
    assert audio_bytes is not None
    assert len(audio_bytes) > 1000  # Valid MP3 data generated


def test_voice_review_feedback_generation():
    audio_bytes, path = VoiceService.generate_review_voice_feedback(
        submission_id=999,
        task_title="Customer Analytics Dashboard",
        completeness_pct=85.0,
        good_points=["Submitted on time", "Clean code structure"],
        not_good_points=["Missing architecture diagram"],
        suggested_status="Needs Changes",
    )
    assert audio_bytes is not None
    assert len(audio_bytes) > 1000


def test_gemini_provider_fallback_to_deterministic_engine():
    gemini = GeminiAIProvider(api_key="", model_name="gemini-1.5-flash")
    task = Task(
        task_id="TSK-GEMINI-TEST",
        title="Gemini Verification Test",
        description="Verify Gemini provider graceful handling",
    )
    res = gemini.explain_task(task, language="en")
    assert "what_is_this_task" in res
    assert "step_by_step" in res


def test_what_is_good_vs_not_good_comparison(test_db):
    InternRepository.upsert(
        db=test_db,
        intern_id="INT-COMPARE-1",
        name="Student Builder",
        email="builder@test.com",
        department="Engineering",
    )
    task = TaskService.create_task(
        db=test_db,
        task_id="TSK-COMPARE",
        title="Comparison Matrix Milestone",
        description="Test side-by-side analysis",
        required_documents="app.py, test.py, documentation.pdf",
    )
    TaskService.bulk_allocate_task(test_db, ["INT-COMPARE-1"], "TSK-COMPARE")

    # Submit app.py but omit documentation.pdf and test.py
    sub = SubmissionService.handle_submission(
        db=test_db,
        intern_id="INT-COMPARE-1",
        task_id="TSK-COMPARE",
        uploaded_files=[("app.py", b"print('Hello world')")],
        link_url="https://github.com/internflow/compare",
    )

    report = VerificationService.run_verification(
        db=test_db,
        submission_id=sub.id,
    )

    # Check report has good_points and not_good_points
    assert report.good_points is not None
    assert report.not_good_points is not None
    assert "app.py" in report.good_points or "Submission" in report.good_points
    assert "documentation.pdf" in report.not_good_points or "test.py" in report.not_good_points

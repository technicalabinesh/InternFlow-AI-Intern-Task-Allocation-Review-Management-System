"""Tests for Email Safety, Demo Mode Guarantees, and Idempotency."""

import pytest
from services.email_service import EmailService, MockEmailProvider


def test_demo_mode_guarantees_mock_provider(monkeypatch):
    import config.settings as settings
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "mock")
    provider = EmailService.get_provider()
    assert isinstance(provider, MockEmailProvider)


def test_mock_provider_simulates_send():
    provider = MockEmailProvider()
    success, status, msg_id = provider.send(
        recipient_email="intern.test@example.com",
        recipient_name="Test Intern",
        subject="Test Subject",
        html_body="<p>Test Body</p>",
        plain_body="Test Body",
    )
    assert success is True
    assert status == "Simulated"
    assert msg_id.startswith("sim-")


def test_template_variable_substitution():
    context = {
        "Intern_Name": "Rohan Verma",
        "Task_Title": "Dockerize Backend Service",
        "Task_ID": "TSK-302",
        "Deadline": "2026-11-15",
    }
    subject, html_body, plain_body = EmailService.render_template("new_assignment", context)

    assert "Dockerize Backend Service" in subject
    assert "Rohan Verma" in plain_body
    assert "2026-11-15" in plain_body
    assert "TSK-302" in plain_body
    assert "{{Intern_Name}}" not in plain_body


def test_idempotency_key_deterministic():
    key1 = EmailService.calculate_idempotency_key(
        recipient="user@example.com",
        template_type="new_assignment",
        task_id="TSK-100",
        trigger_date="2026-10-26",
    )
    key2 = EmailService.calculate_idempotency_key(
        recipient="user@example.com",
        template_type="new_assignment",
        task_id="TSK-100",
        trigger_date="2026-10-26",
    )
    assert key1 == key2
    assert len(key1) == 64  # SHA-256 hex length

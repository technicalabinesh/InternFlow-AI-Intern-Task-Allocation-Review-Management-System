"""Tests for Role-Based Access Control (RBAC) and Permissions."""

import pytest
from database.models import User


def check_permission(user_role: str, action: str) -> bool:
    """RBAC matrix enforcement."""
    permissions = {
        "admin": [
            "manage_interns",
            "import_excel",
            "export_excel",
            "create_task",
            "allocate_task",
            "send_batch_emails",
            "schedule_review",
            "view_audit_logs",
            "configure_settings",
            "view_all_submissions",
        ],
        "mentor": [
            "view_assigned_interns",
            "review_submissions",
            "approve_submission",
            "request_changes",
            "edit_feedback",
            "schedule_review",
            "export_excel",
        ],
        "intern": [
            "view_own_tasks",
            "read_ai_instructions",
            "submit_work",
            "view_own_feedback",
            "view_own_schedule",
        ],
    }
    return action in permissions.get(user_role, [])


def test_admin_has_full_management_permissions():
    assert check_permission("admin", "import_excel") is True
    assert check_permission("admin", "allocate_task") is True
    assert check_permission("admin", "view_audit_logs") is True


def test_mentor_cannot_import_excel_or_configure_settings():
    assert check_permission("mentor", "review_submissions") is True
    assert check_permission("mentor", "approve_submission") is True
    assert check_permission("mentor", "import_excel") is False
    assert check_permission("mentor", "configure_settings") is False


def test_intern_cannot_approve_or_allocate():
    assert check_permission("intern", "submit_work") is True
    assert check_permission("intern", "read_ai_instructions") is True
    assert check_permission("intern", "approve_submission") is False
    assert check_permission("intern", "allocate_task") is False
    assert check_permission("intern", "view_audit_logs") is False

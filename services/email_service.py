"""Email Automation Service for InternFlow AI.

Supports Gmail API with OAuth 2.0, provider abstraction, HTML/Plain templating,
safe mock/demo mode, idempotency duplicate prevention, rate limiting, and audit logging.
"""

from __future__ import annotations

import os
import base64
import hashlib
import datetime
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config.settings import (
    EMAIL_PROVIDER,
    GMAIL_CLIENT_SECRETS_FILE,
    GMAIL_TOKEN_FILE,
    EMAIL_SENDER_NAME,
    EMAIL_SENDER_ADDRESS,
    GMAIL_USER,
    GMAIL_APP_PASSWORD,
    EMAIL_RATE_LIMIT_PER_MINUTE,
    EMAIL_TEST_RECIPIENT,
    DEMO_MODE,
    BASE_DIR,
)
from database.models import EmailLog, TaskAssignment, Intern, Task
from database.connection import get_db

TEMPLATES_DIR = BASE_DIR / "templates"


TEMPLATES_CATALOG = {
    "new_assignment": {
        "title": "New Task Assignment",
        "subject": "Your Internship Task — {{Task_Title}}",
        "template_file": "assignment_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "Your new internship task has been assigned.\n\n"
            "Task: {{Task_Title}} (ID: {{Task_ID}})\n"
            "Priority: {{Task_Priority}}\n"
            "Deadline: {{Deadline}}\n\n"
            "What you need to do:\n{{Simplified_Task_Explanation}}\n\n"
            "Required documents:\n{{Required_Documents}}\n\n"
            "Review date: {{Review_Date}}\n"
            "Review time: {{Review_Time}}\n"
            "Meeting link: {{Meeting_Link}}\n\n"
            "Submit your completed work here:\n{{Submission_Instructions}}\n\n"
            "Please review the requirements and complete your submission before the deadline.\n\n"
            "Regards,\nInternship Coordination Team"
        ),
    },
    "simplified_instructions": {
        "title": "Simplified Task Instructions",
        "subject": "Simplified Instructions for Task: {{Task_Title}}",
        "template_file": "assignment_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "Here are the simplified step-by-step instructions for your assigned task '{{Task_Title}}':\n\n"
            "{{Simplified_Task_Explanation}}\n\n"
            "Due Date: {{Deadline}}\n"
            "Please reach out if you have any questions.\n\n"
            "Regards,\nInternFlow AI Mentorship Team"
        ),
    },
    "deadline_reminder": {
        "title": "Upcoming Deadline Reminder",
        "subject": "REMINDER: Task Deadline Approaching — {{Task_Title}}",
        "template_file": "review_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "This is a friendly reminder that the submission deadline for your task '{{Task_Title}}' is approaching on {{Deadline}}.\n\n"
            "Required Deliverables: {{Required_Documents}}\n"
            "Submission Link: {{Submission_Instructions}}\n\n"
            "Please ensure all acceptance criteria are met prior to uploading.\n\n"
            "Regards,\nInternship Coordination Team"
        ),
    },
    "overdue_notice": {
        "title": "Overdue Task Notification",
        "subject": "URGENT: Task Past Due — {{Task_Title}}",
        "template_file": "assignment_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "The deadline for your assigned task '{{Task_Title}}' was {{Deadline}}, and we have not recorded a complete submission.\n\n"
            "Please upload your work immediately or contact your mentor ({{Mentor_Email}}) to discuss an extension.\n\n"
            "Regards,\nInternship Management Office"
        ),
    },
    "review_invitation": {
        "title": "Review Meeting Invitation",
        "subject": "Review Meeting Scheduled: {{Task_Title}}",
        "template_file": "review_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "Your milestone review meeting for '{{Task_Title}}' has been confirmed.\n\n"
            "Date: {{Review_Date}}\n"
            "Time: {{Review_Time}} ({{Timezone}})\n"
            "Meeting Link: {{Meeting_Link}}\n"
            "Mentor: {{Mentor_Email}}\n\n"
            "Please have your code, demo, and slides ready.\n\n"
            "Regards,\nReview Coordination Team"
        ),
    },
    "missing_documents": {
        "title": "Missing Document Notification",
        "subject": "Action Required: Missing Deliverables for {{Task_Title}}",
        "template_file": "feedback_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "Our automated verification noted that some required deliverables are missing from your submission for '{{Task_Title}}'.\n\n"
            "Missing Items:\n{{Mentor_Feedback}}\n\n"
            "Please resubmit the missing files before the scheduled review.\n\n"
            "Regards,\nInternFlow AI Verification Engine"
        ),
    },
    "submission_received": {
        "title": "Submission Received Confirmation",
        "subject": "Submission Received — {{Task_Title}}",
        "template_file": "feedback_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "We have successfully received your submission for '{{Task_Title}}'.\n\n"
            "Submission Time: {{Assigned_Date}}\n"
            "Status: Under Review\n\n"
            "Your mentor will review your work and provide feedback shortly.\n\n"
            "Regards,\nInternFlow AI System"
        ),
    },
    "changes_requested": {
        "title": "Changes Requested",
        "subject": "Revisions Requested: {{Task_Title}}",
        "template_file": "feedback_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "Your mentor has reviewed your submission for '{{Task_Title}}' and requested revisions.\n\n"
            "Mentor Feedback:\n{{Mentor_Feedback}}\n\n"
            "Next Review Date: {{Next_Review_Date}} at {{Next_Review_Time}}\n"
            "Next Meeting Link: {{Next_Meeting_Link}}\n\n"
            "Please make the necessary changes and resubmit your updated work.\n\n"
            "Regards,\nInternship Mentorship Team"
        ),
    },
    "task_approved": {
        "title": "Task Approved",
        "subject": "Congratulations! Task Approved: {{Task_Title}}",
        "template_file": "feedback_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "Great work! Your submission for '{{Task_Title}}' has been officially approved by your mentor.\n\n"
            "Feedback:\n{{Mentor_Feedback}}\n\n"
            "Keep up the great momentum for your next milestone!\n\n"
            "Regards,\nInternship Coordination Team"
        ),
    },
    "next_review_scheduled": {
        "title": "Next Review Scheduled",
        "subject": "Follow-Up Review Scheduled: {{Task_Title}}",
        "template_file": "feedback_email.html",
        "default_text": (
            "Hi {{Intern_Name}},\n\n"
            "Your follow-up review for '{{Task_Title}}' has been scheduled.\n\n"
            "Date: {{Next_Review_Date}} at {{Next_Review_Time}}\n"
            "Meeting Link: {{Next_Meeting_Link}}\n\n"
            "Regards,\nInternship Mentorship Team"
        ),
    },
}


class BaseEmailProvider:
    def send(self, recipient_email: str, recipient_name: str, subject: str, html_body: str, plain_body: str) -> Tuple[bool, str, Optional[str]]:
        """Returns (success: bool, status_label: str, message_id_or_error: Optional[str])."""
        raise NotImplementedError


class MockEmailProvider(BaseEmailProvider):
    """Safe Mock Provider for Demo Mode and offline environments."""

    def send(self, recipient_email: str, recipient_name: str, subject: str, html_body: str, plain_body: str) -> Tuple[bool, str, Optional[str]]:
        simulated_msg_id = f"sim-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(recipient_email.encode()).hexdigest()[:8]}"
        return True, "Simulated", simulated_msg_id


class GmailSMTPProvider(BaseEmailProvider):
    """Real Gmail sender using SMTP with Google App Password (TLS port 587)."""

    def __init__(self, username: str, app_password: str):
        self.username = username or EMAIL_SENDER_ADDRESS
        self.app_password = (app_password or "").replace(" ", "").strip()

    def send(self, recipient_email: str, recipient_name: str, subject: str, html_body: str, plain_body: str) -> Tuple[bool, str, Optional[str]]:
        if not self.app_password:
            return False, "Failed", "Gmail App Password is missing. Please enter your 16-character Google App Password in Settings > Email Integration."

        try:
            message = MIMEMultipart("alternative")
            message["to"] = f"{recipient_name} <{recipient_email}>" if recipient_name else recipient_email
            message["from"] = f"{EMAIL_SENDER_NAME} <{self.username}>"
            message["subject"] = subject

            part1 = MIMEText(plain_body, "plain", "utf-8")
            part2 = MIMEText(html_body, "html", "utf-8")
            message.attach(part1)
            message.attach(part2)

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
                server.starttls()
                server.login(self.username, self.app_password)
                server.sendmail(self.username, [recipient_email], message.as_string())

            msg_id = f"smtp-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(recipient_email.encode()).hexdigest()[:8]}"
            return True, "Sent", msg_id
        except smtplib.SMTPAuthenticationError:
            return False, "Failed", "Gmail SMTP authentication failed. Please verify your Google email address and ensure you generated a 16-character App Password (https://myaccount.google.com/apppasswords)."
        except Exception as e:
            return False, "Failed", f"SMTP delivery error: {str(e)}"


class GmailOAuthProvider(BaseEmailProvider):
    """Real Gmail API sender using OAuth 2.0 credentials."""

    def __init__(self, client_secrets_file: str, token_file: str):
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self._service = None

    def _get_service(self):
        if self._service:
            return self._service
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
            creds = None

            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(self.client_secrets_file):
                    flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                    try:
                        creds = flow.run_local_server(port=8080)
                    except Exception:
                        creds = flow.run_local_server(port=0)
                    with open(self.token_file, "w") as token:
                        token.write(creds.to_json())

            if creds:
                self._service = build("gmail", "v1", credentials=creds)
                return self._service
        except Exception as e:
            pass
        return None

    def send(self, recipient_email: str, recipient_name: str, subject: str, html_body: str, plain_body: str) -> Tuple[bool, str, Optional[str]]:
        service = self._get_service()
        if not service:
            return False, "Failed", "Gmail OAuth token not authorized. Click 'Authorize Gmail' or provide a 16-character Google App Password for instant delivery."

        try:
            message = MIMEMultipart("alternative")
            message["to"] = f"{recipient_name} <{recipient_email}>" if recipient_name else recipient_email
            message["from"] = f"{EMAIL_SENDER_NAME} <{EMAIL_SENDER_ADDRESS}>"
            message["subject"] = subject

            part1 = MIMEText(plain_body, "plain", "utf-8")
            part2 = MIMEText(html_body, "html", "utf-8")
            message.attach(part1)
            message.attach(part2)

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            sent = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
            return True, "Sent", sent.get("id")
        except Exception as e:
            return False, "Failed", str(e)


class EmailService:
    @classmethod
    def get_provider(cls) -> BaseEmailProvider:
        import config.settings as conf
        demo_mode = getattr(conf, "DEMO_MODE", False)
        provider_name = getattr(conf, "EMAIL_PROVIDER", "mock").lower()

        if demo_mode or provider_name == "mock":
            return MockEmailProvider()

        # Check environment variables / settings
        app_pwd = (os.getenv("GMAIL_APP_PASSWORD") or getattr(conf, "GMAIL_APP_PASSWORD", "") or "").strip()
        user_email = (os.getenv("GMAIL_USER") or getattr(conf, "GMAIL_USER", "") or getattr(conf, "EMAIL_SENDER_ADDRESS", "") or "m.abinesh555@gmail.com").strip()

        # If App Password is provided, prefer SMTP for instant zero-friction delivery
        if app_pwd:
            return GmailSMTPProvider(user_email, app_pwd)

        # Otherwise try OAuth credentials
        if os.path.exists(conf.GMAIL_TOKEN_FILE) or os.path.exists(conf.GMAIL_CLIENT_SECRETS_FILE):
            return GmailOAuthProvider(conf.GMAIL_CLIENT_SECRETS_FILE, conf.GMAIL_TOKEN_FILE)

        return MockEmailProvider()

    @classmethod
    def render_template(cls, template_type: str, context: Dict[str, Any]) -> Tuple[str, str, str]:
        """Render subject, HTML body, and plain-text body with substituted context variables."""
        cfg = TEMPLATES_CATALOG.get(template_type, TEMPLATES_CATALOG["new_assignment"])
        subject_tpl = cfg["subject"]
        text_tpl = cfg["default_text"]
        template_file = cfg.get("template_file", "assignment_email.html")

        # Fallback values for context placeholders
        safe_ctx = {
            "Intern_Name": "Intern",
            "Task_Title": "Assigned Task",
            "Task_ID": "TSK-000",
            "Task_Priority": "Medium",
            "Assigned_Date": datetime.date.today().strftime("%Y-%m-%d"),
            "Deadline": "TBD",
            "Simplified_Task_Explanation": "Please refer to task dashboard for details.",
            "Required_Documents": "Source code & documentation",
            "Submission_Instructions": "Submit link or archive via portal.",
            "Review_Date": "TBD",
            "Review_Time": "10:00 AM",
            "Meeting_Link": "https://meet.google.com/xyz",
            "Mentor_Email": "mentor@internflow.ai",
            "Submission_Status": "Submitted",
            "Verification_Status": "Pending",
            "Mentor_Feedback": "No feedback yet.",
            "Next_Review_Date": "",
            "Next_Review_Time": "",
            "Next_Meeting_Link": "",
            "Timezone": "Asia/Kolkata",
        }
        safe_ctx.update({k: str(v) for k, v in context.items() if v is not None})

        # Render subject
        subject = subject_tpl
        for k, v in safe_ctx.items():
            subject = subject.replace(f"{{{{{k}}}}}", str(v))

        # Render plain text
        plain_body = text_tpl
        for k, v in safe_ctx.items():
            plain_body = plain_body.replace(f"{{{{{k}}}}}", str(v))

        # Render HTML
        html_path = TEMPLATES_DIR / template_file
        if html_path.exists():
            html_raw = html_path.read_text(encoding="utf-8")
            html_body = html_raw
            for k, v in safe_ctx.items():
                html_body = html_body.replace(f"{{{{{k}}}}}", str(v))
        else:
            html_body = f"<html><body><pre>{plain_body}</pre></body></html>"

        return subject, html_body, plain_body

    @classmethod
    def calculate_idempotency_key(cls, recipient: str, template_type: str, task_id: str, trigger_date: Optional[str] = None) -> str:
        date_str = trigger_date or datetime.date.today().strftime("%Y-%m-%d")
        raw = f"{recipient.lower()}:{template_type}:{task_id}:{date_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def send_email(
        cls,
        recipient_email: str,
        recipient_name: str,
        template_type: str,
        context: Dict[str, Any],
        task_id: str = "GEN",
        force_send: bool = False,
    ) -> Tuple[bool, str, str]:
        """Send a single email with idempotency protection and database logging.

        Returns: (success: bool, status: str, message: str)
        """
        idempotency_key = cls.calculate_idempotency_key(
            recipient=recipient_email,
            template_type=template_type,
            task_id=task_id,
        )

        with get_db() as db:
            # Check idempotency unless force_send is requested
            if not force_send:
                existing = db.query(EmailLog).filter(EmailLog.idempotency_key == idempotency_key).first()
                if existing and existing.status in ("Sent", "Simulated"):
                    return True, existing.status, f"Duplicate prevented: email already logged ({existing.status}) today."

            subject, html_body, plain_body = cls.render_template(template_type, context)
            provider = cls.get_provider()

            success, status_label, msg_or_err = provider.send(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                subject=subject,
                html_body=html_body,
                plain_body=plain_body,
            )

            email_log = EmailLog(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                template_type=template_type,
                subject=subject,
                body_preview=plain_body[:300] + ("..." if len(plain_body) > 300 else ""),
                idempotency_key=idempotency_key,
                status=status_label,
                provider="mock" if isinstance(provider, MockEmailProvider) else "gmail",
                message_id=msg_or_err if success else None,
                error_message=None if success else msg_or_err,
                sent_at=datetime.datetime.utcnow(),
            )
            db.add(email_log)

            # Update assignment last email status if available
            assignment = db.query(TaskAssignment).filter(
                TaskAssignment.intern_id == context.get("Intern_ID", ""),
                TaskAssignment.task_id == task_id,
            ).first()
            if assignment:
                assignment.last_email_status = status_label

            db.commit()

            return success, status_label, msg_or_err or "Email processed successfully."

    @classmethod
    def send_test_email(cls, template_type: str, context: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Send a test email to the designated coordinator address."""
        test_recipient = EMAIL_TEST_RECIPIENT or "coordinator-test@example.com"
        context_copy = dict(context)
        context_copy["Intern_Name"] = f"[TEST] {context_copy.get('Intern_Name', 'Coordinator')}"
        return cls.send_email(
            recipient_email=test_recipient,
            recipient_name="Test Coordinator",
            template_type=template_type,
            context=context_copy,
            task_id="TEST-PREVIEW",
            force_send=True,
        )

    @classmethod
    def batch_send_assignment_emails(
        cls,
        assignments: List[TaskAssignment],
        template_type: str = "new_assignment",
        force_send: bool = False,
    ) -> Dict[str, int]:
        """Send emails in batch with rate limiting protection."""
        stats = {"sent": 0, "simulated": 0, "failed": 0, "skipped": 0}

        for a in assignments:
            intern = a.intern
            task = a.task
            if not intern or not task:
                stats["skipped"] += 1
                continue

            ctx = {
                "Intern_ID": a.intern_id,
                "Intern_Name": intern.name,
                "Task_ID": a.task_id,
                "Task_Title": task.title,
                "Task_Priority": task.priority,
                "Assigned_Date": a.assigned_date.strftime("%Y-%m-%d") if a.assigned_date else "",
                "Deadline": a.deadline.strftime("%Y-%m-%d") if a.deadline else "Check Portal",
                "Simplified_Task_Explanation": task.description,
                "Required_Documents": task.required_documents or "Source Code and README",
                "Submission_Instructions": task.submission_instructions or "Submit link via portal",
                "Review_Date": a.review_date.strftime("%Y-%m-%d") if a.review_date else "TBD",
                "Review_Time": a.review_time or "TBD",
                "Meeting_Link": a.meeting_link or "TBD",
                "Mentor_Email": a.mentor_email or "mentor@internflow.ai",
                "Next_Review_Date": a.next_review_date.strftime("%Y-%m-%d") if a.next_review_date else "",
                "Next_Review_Time": a.next_review_time or "",
                "Next_Meeting_Link": a.next_meeting_link or "",
            }

            success, status_label, _ = cls.send_email(
                recipient_email=intern.email,
                recipient_name=intern.name,
                template_type=template_type,
                context=ctx,
                task_id=a.task_id,
                force_send=force_send,
            )

            if status_label == "Sent":
                stats["sent"] += 1
            elif status_label == "Simulated":
                stats["simulated"] += 1
            else:
                stats["failed"] += 1

            # Respect rate limit
            time.sleep(0.05)

        return stats

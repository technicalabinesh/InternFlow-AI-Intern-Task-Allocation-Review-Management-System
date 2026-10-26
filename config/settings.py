"""Settings configuration for InternFlow AI.

Manages environment variables, default settings, and secure configurations.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

# Base Directory of Project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# App Configuration
APP_NAME = os.getenv("APP_NAME", "InternFlow AI")
APP_ENV = os.getenv("APP_ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "internflow-ai-super-secret-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Demo Mode Configuration
# When DEMO_MODE is True, all emails are simulated, and mock AI is available without API keys
DEMO_MODE = os.getenv("DEMO_MODE", "True").lower() in ("true", "1", "yes")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'internflow.db'}")

# Storage Paths
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage")))
UPLOADS_DIR = STORAGE_DIR / "uploads"
EXPORTS_DIR = STORAGE_DIR / "exports"
TEMPLATES_DIR = STORAGE_DIR / "templates"
AUDIO_DIR = STORAGE_DIR / "audio"

# Ensure storage directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file upload limit in MB
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# AI Configuration (Google Gemini by default)
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
AI_MODEL = os.getenv("AI_MODEL", "gemini-3.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Google Cloud Project Configuration
GOOGLE_PROJECT_NAME = os.getenv("GOOGLE_PROJECT_NAME", "Demo")
GOOGLE_PROJECT_NUMBER = os.getenv("GOOGLE_PROJECT_NUMBER", "725871401580")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "modern-setting-465202-s4")
GMAIL_API_KEY = os.getenv("GMAIL_API_KEY", "")

# Email Configuration
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "mock").lower()
GMAIL_CLIENT_SECRETS_FILE = os.getenv("GMAIL_CLIENT_SECRETS_FILE", str(BASE_DIR / "credentials.json"))
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", str(BASE_DIR / "token.json"))
EMAIL_SENDER_NAME = os.getenv("EMAIL_SENDER_NAME", "InternFlow AI Coordinator")
EMAIL_SENDER_ADDRESS = os.getenv("EMAIL_SENDER_ADDRESS", "coordinator@example.com")
EMAIL_RATE_LIMIT_PER_MINUTE = int(os.getenv("EMAIL_RATE_LIMIT_PER_MINUTE", "30"))
EMAIL_TEST_RECIPIENT = os.getenv("EMAIL_TEST_RECIPIENT", "coordinator-test@example.com")

# Timezone
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Asia/Kolkata")

# Allowed upload extensions
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md",
    ".png", ".jpg", ".jpeg", ".zip",
    ".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".json", ".sql"
}

# Excel template headers (24 required columns)
EXCEL_COLUMNS = [
    "Intern_ID",
    "Intern_Name",
    "Email",
    "Department",
    "Mentor_Email",
    "Task_ID",
    "Task_Title",
    "Task_Description",
    "Task_Priority",
    "Assigned_Date",
    "Deadline",
    "Required_Documents",
    "Submission_Instructions",
    "Review_Date",
    "Review_Time",
    "Meeting_Link",
    "Submission_Link",
    "Submission_Status",
    "Verification_Status",
    "Mentor_Feedback",
    "Next_Review_Date",
    "Next_Review_Time",
    "Next_Meeting_Link",
    "Last_Email_Status",
]

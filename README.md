# 🚀 InternFlow AI — Intern Task Allocation & Review Management System

**InternFlow AI** is a production-grade, AI-powered enterprise web application designed to help internship coordinators and mentors manage 100+ interns through a centralized Excel workbook, automatically explain assigned technical tasks in student-friendly terms (English & Tamil), send personalized emails with idempotency deduplication, track multi-version submissions, verify acceptance criteria without executing untrusted code, generate improvement feedback, and schedule milestone review sessions in the Asia/Kolkata timezone.

---

## 🌟 Key System Capabilities

### 1. 👥 Role-Based Access Control (RBAC)
* **Admin / Internship Coordinator**: Bulk allocation, Excel import/export, email dispatch center, mentor reassignment, and audit log inspection.
* **Mentor / Reviewer**: Review assigned submissions, approve/reject/request changes, edit AI-generated feedback, and schedule follow-up reviews.
* **Intern**: View assigned milestones, read simplified 10-point AI instructions (in English or Tamil), upload multi-file or link deliverables (v1, v2...), and track feedback.
* **Quick 1-Click Role Switcher**: Instant evaluation across all three perspectives directly from the UI sidebar in Demo Mode.

### 2. 📊 Centralized Excel Processing (24 Mandatory Columns)
* Full support for `.xlsx` and `.csv` files managing 100+ interns.
* Downloadable **Blank 24-Column Master Template**.
* Downloadable **Pre-populated 105 Sample Interns Dataset** across 5 tracks: Engineering & AI, Frontend, Data Science, Product Design, and Cloud/DevOps.
* **Row-Level Validation Engine**: Detects missing mandatory values, malformed emails, invalid dates, and broken URLs with line numbers and clear explanations.
* **Safe Database Upsert**: Updates existing interns without duplicates or destructive history overwrites.
* **Master Workbook Export**: Generates styled `.xlsx` workbooks with current statuses and review outcomes.

### 3. 💡 AI Task Explanation Engine (10 Questions in EN & TA)
Deconstructs complex technical briefs into student-friendly explanations answering:
1. *What is this task?*
2. *Why are you doing it?*
3. *What exactly must you do?*
4. *Step-by-step instructions*
5. *Tools & technologies required*
6. *Required deliverables, code, screenshots, and reports*
7. *What the final output should look like*
8. *Acceptance criteria*
9. *Submission deadline*
10. *Common mistakes to avoid*
* **Bilingual Support**: Dynamic toggle between **English** and **தமிழ் (Tamil)**.
* **Incomplete Brief Detection**: Automatically flags missing deliverables or unassigned deadlines to the coordinator.
* **Smart Caching**: Explanation outputs are cached in SQLite/PostgreSQL to prevent redundant API calls.

### 4. 🤖 AI Evidence-Based Submission Verification Engine
* Evaluates submitted code, documents, and repository links against mentor acceptance criteria across **Completeness**, **Requirement Compliance**, **Quality**, and **Submission Compliance**.
* **Zero Code Execution**: Uploaded scripts, python files, and documents are safely parsed as passive text to ensure complete system safety against malicious code.
* **Prompt Injection Defense**: Sanitizes untrusted user inputs and blocks prompt override injection attacks.
* **Structured Verification Report**: Outputs completeness percentage gauge, requirement-by-requirement checklist, missing deliverables, potential concerns, and actionable improvement suggestions.
* **Mentor Autonomy**: AI provides recommendations (`Needs Changes`, `Approved`, `Rejected`), while mentors make the final binding decision.

### 5. ✉️ Email Automation & Gmail OAuth 2.0 Integration
* **Provider Abstraction**: Extensible architecture supporting **Gmail OAuth 2.0** and **Safe Mock Simulation Provider**.
* **10+ Pre-built HTML Templates**: New assignments, simplified instructions, upcoming reminders, overdue alerts, review invitations, changes requested, approvals, and follow-ups.
* **Idempotency Protection**: SHA-256 deduplication keys prevent accidental duplicate sends to the same intern on the same day.
* **Safe Demo Mode**: Automatically active by default; renders full HTML MIME emails and logs them as `Simulated` without contacting real inboxes.

### 6. 📅 Review Calendar & Scheduling
* Complete meeting management with default **Asia/Kolkata** timezone support.
* Review outcomes, mentor feedback, next review dates, times, and meeting links are captured and synchronized back to the Excel export.

### 7. 📈 Real-Time Plotly Analytics & Audit Logs
* Interactive KPI metric cards and charts: Status Donut Chart, Department Bar Chart, Mentor Workload Stacked Bars, and Overdue Tracker.
* Immutable audit trail logging every administrative allocation, file upload, mentor review, and email dispatch.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Streamlit, Plotly Express, Custom Vanilla CSS Design System |
| **Backend & Logic** | Python 3.11+, Pandas, OpenPyXL, Pydantic |
| **Database & ORM** | SQLite (WAL Mode) / PostgreSQL with SQLAlchemy 2.0 ORM |
| **AI Providers** | Configurable: Local Mock Engine, OpenAI (`gpt-4o-mini`), Google Gemini, Anthropic |
| **Email Service** | Gmail API (OAuth 2.0), RFC 2822 MIME Engine, Mock Simulation Provider |
| **Testing** | Pytest, Pytest-Mock (21 automated unit and integration tests) |

---

## 📂 Project Architecture

```
internflow-ai/
├── app.py                     # Main Streamlit controller & navigation hub
├── requirements.txt           # Project dependencies
├── .env.example               # Configuration template
├── .env                       # Active runtime configuration
├── internflow.db              # SQLite production database
├── config/
│   ├── __init__.py
│   └── settings.py            # Centralized settings & secrets management
├── database/
│   ├── __init__.py
│   ├── connection.py          # SQLAlchemy session & DB initialization
│   ├── models.py              # 10 core SQLAlchemy models
│   ├── repositories.py        # Clean CRUD repository pattern
│   └── seed_data.py           # Pre-seeds 105 sample interns & tasks
├── services/
│   ├── __init__.py
│   ├── excel_service.py       # 24-col validation, import, export & templates
│   ├── ai_service.py          # 10-point explainer & evidence verification
│   ├── email_service.py       # Gmail OAuth, templates, batch & idempotency
│   ├── task_service.py        # Task creation, bulk allocation & overdue check
│   ├── submission_service.py  # File uploads, link check, versioning & text extraction
│   ├── verification_service.py# Verification orchestration
│   └── review_service.py      # Scheduling, completion & follow-ups
├── templates/
│   ├── assignment_email.html  # HTML assignment email template
│   ├── review_email.html      # HTML review invitation template
│   └── feedback_email.html    # HTML review feedback & outcome template
├── ui/
│   ├── __init__.py
│   ├── styles.py              # Design system CSS & status badge pills
│   ├── auth.py                # Session auth, role guards & 1-click switcher
│   ├── dashboard_view.py      # KPI cards, Plotly charts, real-time tracker
│   ├── interns_view.py        # Intern directory, profile modal, add intern
│   ├── excel_view.py          # Workbook upload, validation, export & templates
│   ├── task_allocation_view.py# Multi-intern selection, bulk allocation
│   ├── task_explanation_view.py# 10 questions in English & Tamil
│   ├── submissions_view.py    # Deliverable uploads, versions v1/v2, link check
│   ├── verification_view.py   # Completeness gauge, criteria evaluation
│   ├── mentor_workspace_view.py# Review desk, editable feedback, decisions
│   ├── calendar_view.py       # Review scheduling in Asia/Kolkata timezone
│   ├── email_center_view.py   # Live email preview, test send, batch campaign
│   ├── analytics_view.py      # Interactive program intelligence charts
│   ├── settings_view.py       # AI provider & Gmail OAuth configuration
│   └── audit_view.py          # System audit trail & JSON inspection
├── storage/
│   ├── uploads/               # Securely partitioned intern submissions
│   ├── exports/               # Exported Excel workbooks
│   └── templates/             # Blank and sample 105-intern workbooks
└── tests/
    ├── __init__.py
    ├── test_excel_import.py       # Validates 24 columns, errors, 105 rows
    ├── test_task_allocation.py    # Bulk allocation, overdue detection
    ├── test_verification.py       # Missing docs, versioning, prompt injection
    ├── test_review_scheduling.py  # Review scheduling, timezone, follow-up
    ├── test_email_safety.py       # Idempotency, demo safety, templates
    └── test_role_permissions.py   # RBAC permissions matrix
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* Python 3.10, 3.11, or 3.12 installed.
* Git installed.

### 2. Installation
Clone the repository and install required packages:
```bash
# Navigate to workspace
cd "c:\Users\Hari\Desktop\Intern Task"

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize Database & Pre-Seed Sample Data
The application will automatically initialize the SQLite database (`internflow.db`) and seed **105 realistic interns** across 5 departments on first run. You can also run the seed script directly:
```bash
python database/seed_data.py
```

### 4. Run Automated Tests
Execute the complete test suite:
```bash
python -m pytest tests/ -v
```
*All 21 unit and integration tests should pass.*

### 5. Launch the Application
Start the Streamlit dashboard:
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your web browser.

---

## 🔑 Demo Accounts & 1-Click Role Switcher

The application comes pre-configured with demo accounts for each role:

| Role | Username | Full Name | Email | Password |
|---|---|---|---|---|
| **Admin (Coordinator)** | `admin` | Dr. Priya Raman | `admin@internflow.ai` | `admin123` |
| **Senior Mentor** | `mentor_sharma` | Vikram Sharma | `mentor.sharma@internflow.ai` | `mentor123` |
| **Design Mentor** | `mentor_anita` | Anita Roy | `mentor.anita@internflow.ai` | `mentor123` |
| **Intern** | `intern_arun` | Arun Kumar | `intern.arun@internflow.ai` | `intern123` |

> 💡 **Tip:** In Demo Mode, you do not need to log in and out manually. Use the **⚡ Quick Role Switcher** in the sidebar to toggle between **Admin**, **Mentor**, and **Intern** with a single click!

---

## ✉️ Gmail OAuth 2.0 Configuration Guide

To enable real Gmail sending (when not in Demo Mode):

1. **Google Cloud Console**:
   * Visit [https://console.cloud.google.com/](https://console.cloud.google.com/) and create a project (e.g., `InternFlow-Mailer`).
   * Enable the **Gmail API** under *APIs & Services > Library*.
2. **Configure OAuth Consent Screen**:
   * Navigate to *APIs & Services > OAuth consent screen*.
   * Select **External**, fill in the App Name and user support email.
   * Add test user email addresses who will test sending.
3. **Create Credentials**:
   * Go to *APIs & Services > Credentials > Create Credentials > OAuth client ID*.
   * Select **Desktop application**.
   * Download the client secret JSON file and rename it to **`credentials.json`** in the project root directory.
4. **Update `.env`**:
   ```ini
   DEMO_MODE=False
   EMAIL_PROVIDER=gmail
   GMAIL_CLIENT_SECRETS_FILE=credentials.json
   GMAIL_TOKEN_FILE=token.json
   EMAIL_SENDER_NAME="InternFlow Coordinator"
   EMAIL_SENDER_ADDRESS="your-email@gmail.com"
   ```
5. On the first email dispatch, a browser window will prompt you to authorize your Google account. A `token.json` file will be created automatically for subsequent headless dispatches.

---

## 🤖 AI Provider Configuration

By default, the application runs in **Mock AI Mode**, which generates context-aware, structured responses in English and Tamil without requiring paid API keys.

To use real LLMs, edit `.env` or configure via **⚙️ Settings & Integrations** in the UI:

### OpenAI
```ini
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

### Google Gemini
```ini
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash
GEMINI_API_KEY=AIzaSy...
```

### Anthropic Claude
```ini
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 🛡️ Security & Defensive Safeguards

* **Passive File Inspection**: Code files (`.py`, `.js`, etc.) and documents (`.pdf`, `.docx`) are extracted as static text strings. Execution of uploaded scripts, Jupyter notebooks, or macros is strictly prohibited.
* **Prompt Injection Sanitization**: Incoming text from student notes or task descriptions is filtered to neutralize prompt override attempts.
* **Idempotent Duplicate Prevention**: Outgoing emails compute an SHA-256 fingerprint from `recipient + template + task_id + date`. Identical emails are not re-sent twice in the same day.
* **Path Traversal Protection**: Uploaded filenames are sanitized using regex filtering to prevent directory traversal attacks.
* **Credential Isolation**: `.env`, `credentials.json`, `token.json`, and database files are protected and excluded in `.gitignore`.

---

## 🧪 Verification & Acceptance Checklist

- [x] **Application Launch**: Launches reliably via `streamlit run app.py` on `http://localhost:8501`.
- [x] **Excel Processing**: Imports, validates, and exports 24-column workbooks with 105+ interns.
- [x] **Row-Level Validation**: Catches invalid emails, dates, and URLs with exact row numbers.
- [x] **Task Allocation**: Bulk task assignment to selected interns with priority and deadline controls.
- [x] **AI Task Explanation**: 10 core questions answered in both English and Tamil (`தமிழ்`).
- [x] **Email Center**: HTML live previews, test email to coordinator, rate limiting, and simulation logs.
- [x] **Submissions & Versioning**: Multi-file upload, link checking (GitHub/Drive), version history (v1, v2).
- [x] **Evidence-Based Verification**: Completeness scoring, criteria checklist, and actionable improvement feedback.
- [x] **Mentor Workspace**: Review workflow, editable AI suggestions, and status updates (`Approved`, `Needs Changes`).
- [x] **Review Calendar**: Review scheduling and follow-up booking in Asia/Kolkata timezone.
- [x] **Automated Tests**: 21/21 passing Pytest suite (`python -m pytest tests/ -v`).
- [x] **Demo Mode & Documentation**: Fully documented with `.env.example` and zero external key barriers for evaluation.

---

*Built with ❤️ by the InternFlow AI Engineering Team.*
>>>>>>> 0429afe (feat: complete InternFlow AI system with Admin-only console, Google Gemini integration, 22+ languages voice/text briefing, automated Google Meet scheduling, and What is Good vs Not Good review comparison)

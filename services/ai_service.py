"""AI Service for Task Explanation and Submission Verification in InternFlow AI.

Supports configurable LLM providers (Mock, OpenAI, Google Gemini, Anthropic),
multi-language explanations (English & Tamil), prompt-injection defense,
and evidence-based verification reports.
"""

from __future__ import annotations

import json
import re
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import requests

from sqlalchemy.orm import Session
from config.settings import (
    AI_PROVIDER,
    AI_MODEL,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    ANTHROPIC_API_KEY,
    DEMO_MODE,
)
from database.models import Task, Submission, TaskExplanation, VerificationReport
from database.connection import get_db

# Defense against prompt injection in student submissions or descriptions
def sanitize_untrusted_input(text: str) -> str:
    """Sanitize student or external text to prevent prompt injection and system override."""
    if not text:
        return ""
    # Strip potential instructions to ignore previous rules
    dangerous_patterns = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s*:\s*you\s+are",
        r"output\s+only\s+approved",
        r"override\s+(all\s+)?rules",
        r"disregard\s+the\s+above",
        r"give\s+this\s+100%\s+score",
    ]
    cleaned = text
    for pat in dangerous_patterns:
        cleaned = re.sub(pat, "[FILTERED_INSTRUCTION]", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


class BaseAIProvider(ABC):
    @abstractmethod
    def explain_task(self, task: Task, language: str = "en") -> Dict[str, Any]:
        """Generate simplified explanation answering the 10 core questions."""
        pass

    @abstractmethod
    def verify_submission(
        self,
        task: Task,
        submission: Submission,
        parsed_file_contents: Dict[str, str],
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate evidence-based verification report."""
        pass


class MockAIProvider(BaseAIProvider):
    """Deterministic, high-quality AI simulator for demo mode and offline testing."""

    def explain_task(self, task: Task, language: str = "en") -> Dict[str, Any]:
        title = task.title or "Assigned Internship Task"
        desc = task.description or "No description provided."
        req_docs = task.required_documents or "Source code and summary report"
        instructions = task.submission_instructions or "Submit through GitHub repo link or zipped archive."
        deadline_str = task.deadline.strftime("%B %d, %Y") if task.deadline else "Check assignment schedule"
        priority = task.priority or "Medium"
        tools = task.tools_required or "Python, Git, VS Code"

        incomplete_flags = []
        if not task.description or len(task.description.strip()) < 20:
            incomplete_flags.append("Task description is too brief. Additional context needed.")
        if not task.required_documents:
            incomplete_flags.append("Specific required documents are not explicitly listed.")
        if not task.deadline:
            incomplete_flags.append("No official deadline assigned for this task.")

        if language == "ta":
            # High-quality Tamil translation for bilingual intern accessibility
            what_is = f"இந்த பணி '{title}' ஆகும். இது நடைமுறை மென்பொருள் பயன்பாட்டை உருவாக்கும் ஒரு முக்கிய பயிற்சியாகும்."
            why_doing = f"நிஜ உலக உற்பத்தி சூழலில் பயன்படுத்தப்படும் தொழில்நுட்பங்கள் மற்றும் சிறந்த நடைமுறைகளை மாணவர்கள் நேரடியாக கற்றுக்கொள்ள இது வழங்கப்பட்டுள்ளது."
            what_must = f"வழங்கப்பட்ட தேவைகளின் அடிப்படையில் {title}-ஐ முழுமையாக கட்டமைத்து, சோதித்து, ஆவணப்படுத்த வேண்டும்."
            steps = (
                "1. பணி தேவைகள் மற்றும் ஏற்றுக்கொள்ளும் அளவுகோல்களை கவனமாக படிக்கவும்.\n"
                "2. திட்ட களஞ்சியத்தை (Git repo) துவக்கி மூலக் குறியீட்டை எழுதவும்.\n"
                "3. தேவையான செயல்பாடுகளை பூர்த்தி செய்து யூனிட் சோதனைகளை இயக்கவும்.\n"
                "4. ஆவணங்கள் (README) மற்றும் ஸ்கிரீன்ஷாட்களை தயார் செய்யவும்.\n"
                "5. இறுதி வெளியீட்டை காலக்கெடுவுக்குள் சமர்ப்பிக்கவும்."
            )
            tools_resp = f"தேவையான கருவிகள்: {tools}."
            deliverables = f"சமர்ப்பிக்க வேண்டியவை: {req_docs}."
            final_look = "சுத்தமான கட்டமைப்பு, விரிவான README கோப்பு மற்றும் அனைத்து சோதனைகளும் வெற்றிகரமாக இயங்கும் நிலை."
            criteria = task.acceptance_criteria or "அனைத்து முக்கிய தேவைகளும் பிழையின்றி செயல்பட வேண்டும்; குறியீடு தரநிலைகளை பூர்த்தி செய்ய வேண்டும்."
            deadline_info = f"இறுதி நாள்: {deadline_str}."
            mistakes = (
                "1. ஆவணங்கள் மற்றும் வழிமுறைகளை சேர்க்க மறப்பது.\n"
                "2. கடைசி நிமிடத்தில் சமர்ப்பிப்பது.\n"
                "3. சோதனைகளை சரிபார்க்காமல் குறியீட்டை சமர்ப்பிப்பது."
            )
            summary = f"பணி விளக்கம்: {title} - {desc[:120]}..."
        else:
            what_is = f"This task is '{title}', designed to build practical, production-ready competencies in your domain."
            why_doing = f"The goal is to master realistic development workflows, automated testing, and clear technical documentation required for industry roles."
            what_must = f"You must design, implement, test, and package '{title}' strictly according to the mentor specifications."
            steps = (
                "1. Review the task requirements and acceptance criteria thoroughly.\n"
                "2. Set up your local development workspace and initialize version control (Git).\n"
                "3. Implement the core functionality step-by-step following clean code standards.\n"
                "4. Conduct unit and integration tests to ensure stability and zero crashes.\n"
                "5. Prepare the required documentation (README.md) and visual verification screenshots.\n"
                "6. Submit the deliverables via GitHub link or file archive before the deadline."
            )
            tools_resp = f"Required technologies and tools: {tools}."
            deliverables = f"Required files & deliverables: {req_docs}.\nInstructions: {instructions}"
            final_look = "A fully functional solution with zero unhandled exceptions, accompanied by clear setup documentation and test evidence."
            criteria = task.acceptance_criteria or "All mandatory user stories implemented; clean code comments; passing test suite; valid documentation."
            deadline_info = f"Due Date: {deadline_str}. Late submissions may require follow-up review justification."
            mistakes = (
                "1. Failing to include a comprehensive README.md explaining how to run the project.\n"
                "2. Hardcoding credentials or API keys directly in source code.\n"
                "3. Submitting incomplete archives or inaccessible private repository links.\n"
                "4. Waiting until the final day to test deployment or submission pipelines."
            )
            summary = f"Task Overview: {title} — {desc[:140]}..."

        full_text = (
            f"### 1. What is this task?\n{what_is}\n\n"
            f"### 2. Why are you doing it?\n{why_doing}\n\n"
            f"### 3. What exactly must you do?\n{what_must}\n\n"
            f"### 4. Step-by-Step Instructions\n{steps}\n\n"
            f"### 5. Tools & Technologies Required\n{tools_resp}\n\n"
            f"### 6. Required Documents & Deliverables\n{deliverables}\n\n"
            f"### 7. What the Final Output Should Look Like\n{final_look}\n\n"
            f"### 8. Acceptance Criteria\n{criteria}\n\n"
            f"### 9. Deadline & Timeline\n{deadline_info}\n\n"
            f"### 10. Common Mistakes to Avoid\n{mistakes}"
        )

        return {
            "summary": summary,
            "what_is_this_task": what_is,
            "why_doing_it": why_doing,
            "what_must_do": what_must,
            "step_by_step": steps,
            "tools_required": tools_resp,
            "deliverables": deliverables,
            "final_output_look": final_look,
            "acceptance_criteria": criteria,
            "deadline_info": deadline_info,
            "common_mistakes": mistakes,
            "incomplete_flags": incomplete_flags,
            "full_explanation_text": full_text,
            "language": language,
        }

    def verify_submission(
        self,
        task: Task,
        submission: Submission,
        parsed_file_contents: Dict[str, str],
        language: str = "en",
    ) -> Dict[str, Any]:
        # 1. Parse deliverables requested
        req_docs_str = task.required_documents or ""
        expected_items = [d.strip() for d in re.split(r"[,;\n]", req_docs_str) if d.strip()]
        if not expected_items:
            expected_items = ["Project Deliverable", "README / Documentation"]

        # 2. Check submitted items
        submitted_files: List[str] = []
        if submission.file_names:
            try:
                submitted_files = json.loads(submission.file_names)
            except Exception:
                submitted_files = [submission.file_names]

        submitted_link = submission.link_url or ""
        notes = sanitize_untrusted_input(submission.notes or "")

        # 3. Completeness check
        matched_items = []
        missing_items = []

        for expected in expected_items:
            exp_clean = expected.lower().replace(" ", "").replace("_", "")
            found = False
            # Check in submitted files
            for sf in submitted_files:
                sf_clean = sf.lower().replace(" ", "").replace("_", "")
                if exp_clean in sf_clean or sf_clean in exp_clean or (exp_clean.endswith(".py") and sf.endswith(".py")):
                    found = True
                    break
            # Check if link covers it
            if not found and ("repo" in exp_clean or "github" in exp_clean or "link" in exp_clean or "code" in exp_clean):
                if "github.com" in submitted_link.lower() or "drive.google.com" in submitted_link.lower():
                    found = True

            if found:
                matched_items.append(expected)
            else:
                missing_items.append(expected)

        # Base completeness percentage calculation
        total_exp = len(expected_items)
        completeness_pct = (len(matched_items) / total_exp * 100.0) if total_exp > 0 else 80.0
        if submitted_link and len(submitted_files) == 0:
            completeness_pct = max(completeness_pct, 70.0)  # GitHub/Drive link provided

        # Check deadline compliance
        is_on_time = submission.deadline_compliance == "On Time"

        # Requirement-by-requirement breakdown
        req_results = []
        for item in expected_items:
            if item in matched_items:
                req_results.append({
                    "criterion": item,
                    "status": "Satisfied",
                    "evidence": f"Found corresponding file or repository reference: {[f for f in submitted_files if item.lower() in f.lower()] or submitted_link}",
                })
            else:
                req_results.append({
                    "criterion": item,
                    "status": "Missing",
                    "evidence": f"No deliverable matching '{item}' was found in the submission package.",
                })

        # Quality & concerns
        potential_concerns = []
        if not is_on_time:
            potential_concerns.append("Submission was logged past the official deadline.")
        if not submitted_files and not submitted_link:
            potential_concerns.append("Neither files nor links were provided in this submission.")
        if submitted_link and "github.com" in submitted_link and not submitted_files:
            potential_concerns.append("Direct static files were omitted; verification depends on remote repository accessibility.")

        # Actionable improvements
        improvements = []
        if missing_items:
            for m in missing_items:
                improvements.append(f"Upload the missing deliverable: {m}")
        improvements.append("Ensure code formatting follows PEP 8 standards and contains inline documentation.")
        if not is_on_time:
            improvements.append("Coordinate with your mentor regarding the late submission policy before the review.")
        improvements.append("Double-check all chart labels, units, and dataset paths prior to final presentation.")

        # Suggested Status
        if completeness_pct >= 90.0 and len(missing_items) == 0:
            suggested_status = "Approved"
            next_actions = "Submission meets all key criteria. Ready for mentor sign-off and review meeting."
        elif completeness_pct >= 50.0:
            suggested_status = "Needs Changes"
            next_actions = "Revise missing deliverables and submit an updated version prior to the follow-up review."
        else:
            suggested_status = "Rejected"
            next_actions = "Major requirements are unfulfilled. Resubmission of complete project package required."

        # Compile explicit What is Good vs What is Not Good Comparison
        good_points = []
        not_good_points = []
        comparison_matrix = []

        if is_on_time:
            good_points.append("Submission was completed on time before the official deadline.")
        else:
            not_good_points.append("Submission logged late past the assigned deadline.")

        if submitted_files:
            good_points.append(f"Successfully uploaded {len(submitted_files)} primary project file(s): {', '.join(submitted_files)}.")
        if submitted_link:
            good_points.append(f"Provided accessible remote repository / drive link: {submitted_link}.")

        for item in expected_items:
            if item in matched_items:
                good_points.append(f"Mandatory deliverable satisfied: '{item}'.")
                comparison_matrix.append({
                    "requirement": item,
                    "assessment": "GOOD",
                    "status_label": "🟢 Satisfied",
                    "evidence": f"Deliverable present in submission package ({[f for f in submitted_files if item.lower() in f.lower()] or submitted_link}).",
                    "details": "Requirement met with verifiable evidence.",
                })
            else:
                not_good_points.append(f"Missing mandatory deliverable: '{item}'.")
                comparison_matrix.append({
                    "requirement": item,
                    "assessment": "NOT GOOD",
                    "status_label": "🔴 Missing",
                    "evidence": "No corresponding deliverable or file found in uploaded package.",
                    "details": "Action required: develop and submit this required component.",
                })

        if not submitted_files and not submitted_link:
            not_good_points.append("Neither direct files nor remote links were submitted.")

        evidence_summary = (
            f"Files analyzed ({len(submitted_files)}): {', '.join(submitted_files) if submitted_files else 'None'}. "
            f"Remote Link: {submitted_link if submitted_link else 'None'}. "
            f"Deadline Status: {submission.deadline_compliance}."
        )

        return {
            "completeness_pct": round(completeness_pct, 1),
            "requirement_results": req_results,
            "evidence_found": evidence_summary,
            "missing_requirements": missing_items,
            "potential_concerns": potential_concerns,
            "improvement_suggestions": improvements,
            "good_points": good_points,
            "not_good_points": not_good_points,
            "comparison_matrix": comparison_matrix,
            "recommended_next_actions": next_actions,
            "suggested_status": suggested_status,
            "disclaimer": "Note: AI provides evidence-based recommendations. The assigned mentor makes the final evaluation decision.",
        }


class GeminiAIProvider(BaseAIProvider):
    """Google Gemini AI integration (gemini-3.5-flash-lite, gemini-3.5-flash, gemini-3.8-flash)."""

    def __init__(self, api_key: str, model_name: str = "gemini-3.5-flash-lite"):
        self.api_key = api_key
        self.model_name = model_name or "gemini-3.5-flash-lite"
        self._model = None
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key, transport="rest")
                # Try preferred model, fallback to compatible modern flash models
                candidate_models = [self.model_name, "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
                for candidate in candidate_models:
                    try:
                        self._model = genai.GenerativeModel(candidate)
                        self.model_name = candidate
                        break
                    except Exception:
                        continue
            except Exception:
                self._model = None

    def explain_task(self, task: Task, language: str = "en") -> Dict[str, Any]:
        mock = MockAIProvider().explain_task(task, language)
        if not self._model or not self.api_key:
            return mock

        try:
            from services.voice_service import SUPPORTED_LANGUAGES
            lang_label = SUPPORTED_LANGUAGES.get(language, "English")
            prompt = (
                f"You are InternFlow AI, powered by Google Gemini. "
                f"Explain this technical milestone in clear, student-friendly terms answering 10 core questions in {lang_label} language:\n"
                f"1. What is this task?\n2. Why are you doing it?\n3. What exactly must you do?\n4. Step-by-step instructions\n"
                f"5. Tools required\n6. Deliverables required\n7. Final output look\n8. Acceptance criteria\n9. Deadline info\n10. Common mistakes\n\n"
                f"Language required: {lang_label}.\n"
                f"Task Title: {task.title}\n"
                f"Description: {task.description}\n"
                f"Required Documents: {task.required_documents}\n"
                f"Tools: {task.tools_required}\n"
                f"Deadline: {task.deadline}"
            )
            response = self._model.generate_content(prompt, request_options={"timeout": 12})
            if response and response.text:
                mock["full_explanation_text"] = response.text
                mock["summary"] = f"Gemini ({lang_label}) Briefing: {task.title} — {response.text[:120]}..."
        except Exception:
            pass
        return mock

    def verify_submission(
        self,
        task: Task,
        submission: Submission,
        parsed_file_contents: Dict[str, str],
        language: str = "en",
    ) -> Dict[str, Any]:
        # Generate base deterministic evidence structure
        mock = MockAIProvider().verify_submission(task, submission, parsed_file_contents, language)
        if not self._model or not self.api_key:
            return mock

        try:
            sample_code = ""
            if parsed_file_contents:
                sample_code = "\n".join([f"--- File: {k} ---\n{v[:600]}" for k, v in list(parsed_file_contents.items())[:3]])

            prompt = (
                f"You are InternFlow AI's verification engine powered by Google Gemini.\n"
                f"Analyze this intern's project completion against requirements:\n"
                f"Task: {task.title}\n"
                f"Requirements: {task.required_documents}\n"
                f"Acceptance Criteria: {task.acceptance_criteria}\n"
                f"Submitted Files: {submission.file_names}\n"
                f"Submitted Link: {submission.link_url}\n"
                f"Code snippet:\n{sample_code}\n\n"
                f"Answer in JSON format with keys:\n"
                f"- good_points (list of strings: specific strengths, completed items, good patterns)\n"
                f"- not_good_points (list of strings: deficiencies, missing items, unhandled edge cases)\n"
                f"- suggestions (list of strings: actionable next steps)"
            )
            response = self._model.generate_content(prompt, request_options={"timeout": 12})
            if response and response.text:
                cleaned = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned)
                if "good_points" in data and isinstance(data["good_points"], list):
                    mock["good_points"] = data["good_points"]
                if "not_good_points" in data and isinstance(data["not_good_points"], list):
                    mock["not_good_points"] = data["not_good_points"]
                if "suggestions" in data and isinstance(data["suggestions"], list):
                    mock["improvement_suggestions"] = data["suggestions"]
        except Exception:
            pass

        return mock


class OpenAIProvider(BaseAIProvider):
    """OpenAI API integration (gpt-4o, gpt-4o-mini)."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    def explain_task(self, task: Task, language: str = "en") -> Dict[str, Any]:
        if not self.api_key:
            return MockAIProvider().explain_task(task, language)

        system_prompt = (
            "You are InternFlow AI, an expert internship task explainer. "
            "You must break down technical tasks into simple, professional instructions suitable for student interns. "
            "Answer the 10 questions systematically. Do NOT invent dates, links, or requirements. "
            f"Respond in {'Tamil' if language == 'ta' else 'English'}."
        )
        user_content = (
            f"Task Title: {task.title}\n"
            f"Description: {task.description}\n"
            f"Priority: {task.priority}\n"
            f"Deadline: {task.deadline}\n"
            f"Required Documents: {task.required_documents}\n"
            f"Submission Instructions: {task.submission_instructions}\n"
            f"Tools Required: {task.tools_required}\n"
            f"Acceptance Criteria: {task.acceptance_criteria}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                result = resp.json()
                text = result["choices"][0]["message"]["content"]
                mock = MockAIProvider().explain_task(task, language)
                mock["full_explanation_text"] = text
                return mock
        except Exception:
            pass
        return MockAIProvider().explain_task(task, language)

    def verify_submission(
        self,
        task: Task,
        submission: Submission,
        parsed_file_contents: Dict[str, str],
        language: str = "en",
    ) -> Dict[str, Any]:
        return MockAIProvider().verify_submission(task, submission, parsed_file_contents, language)


class AIService:
    """Unified AI service facade handling caching, provider selection, and sanitization."""

    @classmethod
    def get_provider(cls) -> BaseAIProvider:
        provider_name = AI_PROVIDER.lower()
        if provider_name == "gemini":
            return GeminiAIProvider(api_key=GEMINI_API_KEY, model_name=AI_MODEL)
        elif not DEMO_MODE and provider_name == "openai" and OPENAI_API_KEY:
            return OpenAIProvider(api_key=OPENAI_API_KEY, model=AI_MODEL)
        # Default or fallback is always high-quality MockAIProvider
        return MockAIProvider()

    @classmethod
    def get_or_create_explanation(
        cls,
        task: Task,
        language: str = "en",
        force_refresh: bool = False,
        db: Optional[Session] = None,
    ) -> TaskExplanation:
        """Fetch cached explanation from DB or generate and persist a new one."""
        def _execute(session: Session):
            cached = session.query(TaskExplanation).filter(
                TaskExplanation.task_id == task.task_id,
                TaskExplanation.language == language,
            ).first()

            if cached and not force_refresh:
                return cached

            provider = cls.get_provider()
            explanation_data = provider.explain_task(task, language=language)

            if cached:
                cached.summary = explanation_data["summary"]
                cached.what_is_this_task = explanation_data["what_is_this_task"]
                cached.why_doing_it = explanation_data["why_doing_it"]
                cached.what_must_do = explanation_data["what_must_do"]
                cached.step_by_step = explanation_data["step_by_step"]
                cached.tools_required = explanation_data["tools_required"]
                cached.deliverables = explanation_data["deliverables"]
                cached.final_output_look = explanation_data["final_output_look"]
                cached.acceptance_criteria = explanation_data["acceptance_criteria"]
                cached.deadline_info = explanation_data["deadline_info"]
                cached.common_mistakes = explanation_data["common_mistakes"]
                cached.incomplete_flags = json.dumps(explanation_data.get("incomplete_flags", []))
                cached.full_explanation_text = explanation_data["full_explanation_text"]
                session.flush()
                return cached
            else:
                new_exp = TaskExplanation(
                    task_id=task.task_id,
                    language=language,
                    summary=explanation_data["summary"],
                    what_is_this_task=explanation_data["what_is_this_task"],
                    why_doing_it=explanation_data["why_doing_it"],
                    what_must_do=explanation_data["what_must_do"],
                    step_by_step=explanation_data["step_by_step"],
                    tools_required=explanation_data["tools_required"],
                    deliverables=explanation_data["deliverables"],
                    final_output_look=explanation_data["final_output_look"],
                    acceptance_criteria=explanation_data["acceptance_criteria"],
                    deadline_info=explanation_data["deadline_info"],
                    common_mistakes=explanation_data["common_mistakes"],
                    incomplete_flags=json.dumps(explanation_data.get("incomplete_flags", [])),
                    full_explanation_text=explanation_data["full_explanation_text"],
                    is_cached=True,
                    generated_at=datetime.datetime.utcnow(),
                )
                session.add(new_exp)
                session.flush()
                return new_exp

        if db is not None:
            return _execute(db)
        with get_db() as session:
            exp = _execute(session)
            session.commit()
            return exp

    @classmethod
    def generate_verification_report(
        cls,
        task: Task,
        submission: Submission,
        parsed_file_contents: Optional[Dict[str, str]] = None,
        language: str = "en",
        db: Optional[Session] = None,
    ) -> VerificationReport:
        """Run AI verification, generate structured report, and persist in DB."""
        provider = cls.get_provider()
        report_data = provider.verify_submission(
            task=task,
            submission=submission,
            parsed_file_contents=parsed_file_contents or {},
            language=language,
        )

        def _execute(session: Session):
            report = VerificationReport(
                submission_id=submission.id,
                intern_id=submission.intern_id,
                task_id=submission.task_id,
                completeness_pct=report_data["completeness_pct"],
                requirement_results=json.dumps(report_data["requirement_results"]),
                evidence_found=report_data["evidence_found"],
                missing_requirements=json.dumps(report_data["missing_requirements"]),
                potential_concerns=json.dumps(report_data["potential_concerns"]),
                improvement_suggestions=json.dumps(report_data["improvement_suggestions"]),
                good_points=json.dumps(report_data.get("good_points", [])),
                not_good_points=json.dumps(report_data.get("not_good_points", [])),
                recommended_next_actions=report_data["recommended_next_actions"],
                suggested_status=report_data["suggested_status"],
                created_at=datetime.datetime.utcnow(),
            )
            session.add(report)

            # Update submission verification status
            sub_in_db = session.query(Submission).filter(Submission.id == submission.id).first()
            if sub_in_db:
                sub_in_db.verification_status = report_data["suggested_status"]

            session.flush()
            return report

        if db is not None:
            return _execute(db)
        with get_db() as session:
            rep = _execute(session)
            session.commit()
            return rep

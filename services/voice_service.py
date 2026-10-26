"""Voice Service for InternFlow AI with 22+ Languages Support.

Generates AI Voice Briefings for task explanations and project completion reviews
using Google Text-to-Speech (gTTS) and Web Speech API browser integration.
Supports 22 global and regional languages.
"""

from __future__ import annotations

import io
import os
import hashlib
from pathlib import Path
try:
    from gtts import gTTS
except ImportError:
    gTTS = None

from config.settings import AUDIO_DIR


# 22 Global and Regional Languages Catalog
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "flag": "🇬🇧"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "flag": "🇮🇳"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "flag": "🇮🇳"},
    "te": {"name": "Telugu", "native": "తెలుగు", "flag": "🇮🇳"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "flag": "🇮🇳"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "flag": "🇮🇳"},
    "bn": {"name": "Bengali", "native": "বাংলা", "flag": "🇮🇳"},
    "mr": {"name": "Marathi", "native": "मराठी", "flag": "🇮🇳"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "flag": "🇮🇳"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "flag": "🇮🇳"},
    "ur": {"name": "Urdu", "native": "اردو", "flag": "🇵🇰"},
    "es": {"name": "Spanish", "native": "Español", "flag": "🇪🇸"},
    "fr": {"name": "French", "native": "Français", "flag": "🇫🇷"},
    "de": {"name": "German", "native": "Deutsch", "flag": "🇩🇪"},
    "ja": {"name": "Japanese", "native": "日本語", "flag": "🇯🇵"},
    "ko": {"name": "Korean", "native": "한국어", "flag": "🇰🇷"},
    "zh": {"name": "Chinese", "native": "中文", "flag": "🇨🇳"},
    "ar": {"name": "Arabic", "native": "العربية", "flag": "🇸🇦"},
    "pt": {"name": "Portuguese", "native": "Português", "flag": "🇧🇷"},
    "ru": {"name": "Russian", "native": "Русский", "flag": "🇷🇺"},
    "it": {"name": "Italian", "native": "Italiano", "flag": "🇮🇹"},
    "id": {"name": "Indonesian", "native": "Bahasa Indonesia", "flag": "🇮🇩"},
}


class VoiceService:
    @staticmethod
    def get_audio_path(cache_key: str) -> Path:
        """Return the target file path for a cached audio file."""
        safe_key = hashlib.md5(cache_key.encode("utf-8")).hexdigest()
        return AUDIO_DIR / f"{safe_key}.mp3"

    @classmethod
    def generate_task_briefing_audio(
        cls,
        task_id: str,
        task_title: str,
        what_must_do: str,
        step_by_step: str,
        deliverables: str,
        deadline_info: str,
        language: str = "en",
        force_regenerate: bool = False,
    ) -> Tuple[bytes, str]:
        """Generate voice narration explaining the task to the intern in 20+ languages."""
        lang_code = language if language in SUPPORTED_LANGUAGES else "en"
        cache_key = f"task_{task_id}_{lang_code}_{hashlib.md5(what_must_do.encode()).hexdigest()[:6]}"
        audio_path = cls.get_audio_path(cache_key)

        if audio_path.exists() and not force_regenerate:
            return audio_path.read_bytes(), str(audio_path)

        if gTTS is None:
            silent_mp3 = b"\xff\xfb\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00" * 32
            return silent_mp3, str(audio_path)

        clean_steps = step_by_step.replace("\n", " ").replace("###", "").strip()[:350]

        # Multi-language speech scripts
        if lang_code == "ta":
            script = (
                f"வணக்கம்! உங்கள் ஏ.ஐ பணி வழிகாட்டி பேசுகிறேன். "
                f"உங்கள் பணிக்கான தலைப்பு: {task_title}. "
                f"நீங்கள் செய்ய வேண்டியது: {what_must_do}. "
                f"படிமுறை வழிமுறைகள்: {clean_steps}. "
                f"சமர்ப்பிக்க வேண்டிய கோப்புகள்: {deliverables}. "
                f"காலக்கெடு: {deadline_info}. "
                f"வெற்றிகரமாக முடிக்க வாழ்த்துகள்!"
            )
        elif lang_code == "hi":
            script = (
                f"नमस्ते! आपके एआई मेंटर द्वारा कार्य विवरण प्रस्तुत है। "
                f"कार्य का शीर्षक: {task_title}. "
                f"आपको क्या करना है: {what_must_do}. "
                f"महत्वपूर्ण चरण: {clean_steps}. "
                f"जमा करने योग्य दस्तावेज़: {deliverables}. "
                f"अंतिम तिथि: {deadline_info}. "
                f"सफलतापूर्वक पूरा करने के लिए शुभकामनाएं!"
            )
        elif lang_code == "te":
            script = (
                f"నమస్కారం! మీ ఏఐ మెంటార్ టాస్క్ బ్రీఫింగ్. "
                f"టాస్క్ శీర్షిక: {task_title}. "
                f"మీరు చేయవలసిన పనులు: {what_must_do}. "
                f"ముఖ్యమైన దశలు: {clean_steps}. "
                f"సమర్పించాల్సిన ఫైల్స్: {deliverables}. "
                f"గడువు: {deadline_info}. ఆల్ ది బెస్ట్!"
            )
        elif lang_code == "ml":
            script = (
                f"നമസ്കാരം! നിങ്ങളുടെ എഐ മെൻ്റർ നിർദ്ദേശങ്ങൾ. "
                f"പ്രോജക്റ്റ് പേര്: {task_title}. "
                f"നിങ്ങൾ ചെയ്യേണ്ടത്: {what_must_do}. "
                f"സമർപ്പിക്കേണ്ട രേഖകൾ: {deliverables}. "
                f"അവസാന തീയതി: {deadline_info}. ആശംസകൾ!"
            )
        elif lang_code == "es":
            script = (
                f"¡Hola! Bienvenido a tu sesión informativa de mentor de IA para {task_title}. "
                f"Lo que debes hacer: {what_must_do}. "
                f"Pasos principales: {clean_steps}. "
                f"Entregables requeridos: {deliverables}. "
                f"{deadline_info}. ¡Mucho éxito en tu proyecto!"
            )
        elif lang_code == "fr":
            script = (
                f"Bonjour! Bienvenue dans le briefing de votre mentor IA pour {task_title}. "
                f"Ce que vous devez faire: {what_must_do}. "
                f"Étapes clés: {clean_steps}. "
                f"Livrables requis: {deliverables}. "
                f"{deadline_info}. Bonne chance pour votre projet!"
            )
        elif lang_code == "de":
            script = (
                f"Hallo! Willkommen zum KI-Mentor-Briefing für {task_title}. "
                f"Was Sie tun müssen: {what_must_do}. "
                f"Erforderliche Unterlagen: {deliverables}. "
                f"{deadline_info}. Viel Erfolg bei Ihrem Projekt!"
            )
        elif lang_code == "ja":
            script = (
                f"こんにちは！{task_title}に関するAIメンターのブリーフィングへようこそ。"
                f"取り組む内容: {what_must_do}。"
                f"提出物: {deliverables}。"
                f"期限: {deadline_info}。頑張ってください！"
            )
        elif lang_code == "zh":
            script = (
                f"你好！欢迎收听{task_title}的AI导师简报。"
                f"你需要完成的内容: {what_must_do}。"
                f"所需交付物: {deliverables}。"
                f"截止日期: {deadline_info}。祝你顺利完成！"
            )
        else:
            script = (
                f"Hello! Welcome to your AI Mentor voice briefing for {task_title}. "
                f"Here is what you need to do: {what_must_do}. "
                f"Key steps: {clean_steps}. "
                f"Required deliverables: {deliverables}. "
                f"{deadline_info}. "
                f"Follow clean code standards and reach out to your mentor if you need assistance. Good luck!"
            )

        try:
            tts = gTTS(text=script, lang=lang_code, slow=False)
            tts.save(str(audio_path))
            return audio_path.read_bytes(), str(audio_path)
        except Exception:
            # Fallback to English if regional voice endpoint has latency
            tts = gTTS(text=f"Welcome to your task briefing for {task_title}. {what_must_do}", lang="en", slow=False)
            tts.save(str(audio_path))
            return audio_path.read_bytes(), str(audio_path)

    @classmethod
    def generate_review_voice_feedback(
        cls,
        submission_id: int,
        task_title: str,
        completeness_pct: float,
        good_points: List[str],
        not_good_points: List[str],
        improvement_suggestions: Optional[List[str]] = None,
        suggested_status: str = "Under Review",
        language: str = "en",
        force_regenerate: bool = False,
    ) -> Tuple[bytes, str]:
        """Generate voice review summarizing what is good, what is not good, and what to improve in 20+ languages."""
        lang_code = language if language in SUPPORTED_LANGUAGES else "en"
        cache_key = f"review_{submission_id}_{completeness_pct}_{suggested_status}_{lang_code}"
        audio_path = cls.get_audio_path(cache_key)

        if audio_path.exists() and not force_regenerate:
            return audio_path.read_bytes(), str(audio_path)

        if gTTS is None:
            silent_mp3 = b"\xff\xfb\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00" * 32
            return silent_mp3, str(audio_path)

        good_text = " ".join([f"Strength: {g}." for g in good_points[:3]]) if good_points else "Initial project deliverables uploaded."
        not_good_text = " ".join([f"Area needing rework: {ng}." for ng in not_good_points[:3]]) if not_good_points else "No major deficiencies detected."
        improve_text = " ".join([f"Step: {s}." for s in improvement_suggestions[:3]]) if improvement_suggestions else "Prepare demo for your upcoming review."

        if lang_code == "ta":
            script = (
                f"உங்கள் திட்ட சமர்ப்பிப்பு பகுப்பாய்வு முடிவு இதோ. "
                f"முழுமைப் புள்ளி: {round(completeness_pct)} சதவீதம். "
                f"பரிந்துரைக்கப்பட்ட முடிவு: {suggested_status}. "
                f"நீங்கள் சிறப்பாக செய்தவை: {good_text} "
                f"மேம்படுத்த வேண்டியவை: {not_good_text} "
                f"மேற்கொள்ள வேண்டிய முன்னேற்றங்கள்: {improve_text} "
                f"உங்கள் அடுத்த ஆய்வு கூட்டத்தில் மென்டருடன் விவாதிக்கவும்."
            )
        elif lang_code == "hi":
            script = (
                f"आपके प्रोजेक्ट की समीक्षा रिपोर्ट प्रस्तुत है। "
                f"कुल पूर्णता स्कोर: {round(completeness_pct)} प्रतिशत। "
                f"सुझाया गया परिणाम: {suggested_status}। "
                f"आपने जो अच्छा किया: {good_text} "
                f"जिसमें सुधार की आवश्यकता है: {not_good_text} "
                f"सुधार के लिए उठाए जाने वाले कदम: {improve_text}"
            )
        elif lang_code == "es":
            script = (
                f"Aquí está la revisión de finalización de su proyecto para {task_title}. "
                f"Puntuación de integridad: {round(completeness_pct)} por ciento. "
                f"Resultado sugerido: {suggested_status}. "
                f"Lo que hiciste bien: {good_text} "
                f"Lo que no está bien y requiere mejoras: {not_good_text} "
                f"Pasos para mejorar: {improve_text}"
            )
        else:
            script = (
                f"Here is your AI Mentor project completion review for {task_title}. "
                f"Your project scored an overall completeness of {round(completeness_pct)} percent. "
                f"Suggested evaluation outcome is {suggested_status}. "
                f"Here is what is good and completed well: {good_text} "
                f"Here is what is not good and requires rework: {not_good_text} "
                f"What you need to improve next: {improve_text} "
                f"Please review the detailed criteria comparison and prepare for your scheduled review meeting."
            )

        try:
            tts = gTTS(text=script, lang=lang_code, slow=False)
            tts.save(str(audio_path))
            return audio_path.read_bytes(), str(audio_path)
        except Exception:
            tts = gTTS(text=f"Review summary for {task_title}. Completeness: {round(completeness_pct)} percent. Status: {suggested_status}.", lang="en", slow=False)
            tts.save(str(audio_path))
            return audio_path.read_bytes(), str(audio_path)

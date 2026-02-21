"""Service to call Google Gemini (google-generativeai) for summarization.

Uses the modern `GenerativeModel` API and the latest model name
`gemini-1.5-flash-latest`. Calls are executed in a threadpool so the
async FastAPI loop is not blocked.
"""
import logging
import os
import tempfile
from typing import Any
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)


async def summarize_text(conversation: str) -> Any:
    """Summarize a text conversation using Gemini's `gemini-1.5-flash-latest` model.

    Returns a short summary string on success, or a dict {"detail": "..."}
    on failure. Does not raise exceptions.
    """
    api_key = os.getenv("GROQ_API_KEY")
    # Fallback to settings if present (backwards compatibility)
    if not api_key:
        try:
            from app.config.settings import settings

            # Allow using GEMINI_API_KEY as a fallback if GROQ_API_KEY not set
            api_key = os.getenv("GROQ_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        except Exception:
            api_key = None

    if not api_key:
        return {"detail": "Gemini API key not configured"}

    prompt = (
        "You are a concise summarization engine. Return ONLY a short summary (1-2 sentences) of the following text.\n\n"
        + (conversation or "")
    )

    try:
        # Use Groq API for chat completions
        from groq import Groq

        client = Groq(api_key=api_key)

        def call_model():
            print("Calling Groq model...")
            # Build chat completion request per Groq API
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": f"Summarize this conversation:\n{conversation}"}
                ],
            )

            try:
                return response.choices[0].message.content
            except Exception:
                # Fallback to stringified response for debugging
                try:
                    return str(response)
                except Exception:
                    return ""

        raw = await run_in_threadpool(call_model)
        summary = raw.strip() if isinstance(raw, str) else str(raw)
        return summary
    except Exception:
        logger.exception("Gemini text summarization failed")
        return {"detail": "Groq text summarization failed"}


async def summarize_audio(audio_bytes: bytes) -> Any:
    """Summarize audio by sending it to the multimodal Gemini model.

    Sends an instruction plus the binary audio as a multimodal input and
    returns a short summary string or an error dict with `detail` on failure.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            from app.config.settings import settings

            api_key = os.getenv("GROQ_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        except Exception:
            api_key = None

    if not api_key:
        return {"detail": "Gemini API key not configured"}

    try:
        # Transcribe audio first. Check for existing transcription support.
        transcribed_text = None

        # Attempt to use speech_recognition if available as a simple local fallback
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpf:
                tmpf.write(audio_bytes)
                tmpf.flush()
                tmp_path = tmpf.name

            try:
                with sr.AudioFile(tmp_path) as source:
                    audio = recognizer.record(source)
                    transcribed_text = recognizer.recognize_google(audio)
            except Exception:
                transcribed_text = None
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        except Exception:
            transcribed_text = None

        if not transcribed_text:
            # If no transcription available, return informative error
            return {"detail": "Transcription not available. Configure a transcription provider."}

        # Reuse summarize_text to send the transcribed conversation to Groq
        return await summarize_text(transcribed_text)
    except Exception:
        logger.exception("Audio summarization via Groq failed")
        return {"detail": "Groq audio summarization failed"}


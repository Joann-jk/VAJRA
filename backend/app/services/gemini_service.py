"""Service to call Google Gemini (google-generativeai) for summarization.

Uses the modern `GenerativeModel` API and the latest model name
`gemini-1.5-flash-latest`. Calls are executed in a threadpool so the
async FastAPI loop is not blocked.
"""
import logging
import os
from typing import Any
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)


async def summarize_text(conversation: str) -> Any:
    """Summarize a text conversation using Gemini's `gemini-1.5-flash-latest` model.

    Returns a short summary string on success, or a dict {"detail": "..."}
    on failure. Does not raise exceptions.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    # Fallback to settings if present (backwards compatibility)
    if not api_key:
        try:
            from app.config.settings import settings

            api_key = settings.GEMINI_API_KEY
        except Exception:
            api_key = None

    if not api_key:
        return {"detail": "Gemini API key not configured"}

    prompt = (
        "You are a concise summarization engine. Return ONLY a short summary (1-2 sentences) of the following text.\n\n"
        + (conversation or "")
    )

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        def call_model():
            resp = model.generate_content(prompt)
            # New SDK responses expose `.text` for the generated content
            if hasattr(resp, "text") and resp.text:
                return resp.text
            return str(resp)

        raw = await run_in_threadpool(call_model)
        summary = raw.strip() if isinstance(raw, str) else str(raw)
        return summary
    except Exception:
        logger.exception("Gemini text summarization failed")
        return {"detail": "Gemini text summarization failed"}


async def summarize_audio(audio_bytes: bytes) -> Any:
    """Summarize audio by sending it to the multimodal Gemini model.

    Sends an instruction plus the binary audio as a multimodal input and
    returns a short summary string or an error dict with `detail` on failure.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            from app.config.settings import settings

            api_key = settings.GEMINI_API_KEY
        except Exception:
            api_key = None

    if not api_key:
        return {"detail": "Gemini API key not configured"}

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        def call_model():
            resp = model.generate_content([
                "Summarize this audio conversation in 1-2 short sentences.",
                {"mime_type": "audio/mp3", "data": audio_bytes},
            ])
            if hasattr(resp, "text") and resp.text:
                return resp.text
            return str(resp)

        raw = await run_in_threadpool(call_model)
        summary = raw.strip() if isinstance(raw, str) else str(raw)
        return summary
    except Exception:
        logger.exception("Gemini audio summarization failed")
        return {"detail": "Gemini audio summarization failed"}


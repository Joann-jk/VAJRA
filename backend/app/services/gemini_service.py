"""Service to call Google Gemini (via google-generativeai SDK) and return structured JSON.

This module prepares a prompt that instructs Gemini to return ONLY a JSON object
with the requested fields. The output is parsed with a conservative parser to
avoid crashes if Gemini includes extra text.
"""
import logging
from typing import Dict, Any
from starlette.concurrency import run_in_threadpool
import base64

from app.config.settings import settings

logger = logging.getLogger(__name__)


async def summarize_text(conversation: str) -> Any:
    """Summarize a text conversation using Gemini.

    Returns either a string (summary) or a dict like {"error": "..."} on fatal errors.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return {"error": "Gemini API key not configured"}

    prompt = (
        "You are a concise summarization engine. Return ONLY a short summary (1-2 sentences) of the following text.\n\n"
        + conversation
    )

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        def call_model():
            # Prefer generate_text if available
            try:
                resp = genai.generate_text(model="gemini-1.5-flash", input=prompt)
                # Many SDK versions use `.text` or `.content`
                if hasattr(resp, "text") and resp.text:
                    return resp.text
                if hasattr(resp, "content") and resp.content:
                    return resp.content
                return str(resp)
            except Exception:
                # Fallback to chat.create if present
                resp = genai.chat.create(model="gemini-1.5-flash", messages=[{"role": "user", "content": prompt}])
                # Attempt to find text in response
                if hasattr(resp, "candidates") and resp.candidates:
                    return getattr(resp.candidates[0], "content", str(resp))
                return str(resp)

        raw = await run_in_threadpool(call_model)
        # Raw may contain extra whitespace; return a cleaned string
        summary = raw.strip() if isinstance(raw, str) else str(raw)
        return summary
    except Exception as exc:
        logger.exception("Gemini text summarization failed: %s", exc)
        return {"error": f"Gemini text summarization failed: {exc}"}


async def summarize_audio(audio_bytes: bytes) -> Any:
    """Summarize audio by sending it to a multimodal Gemini model.

    This implementation base64-encodes the audio and includes it in the prompt so
    it remains compatible with SDKs that don't expose a dedicated audio input.
    If the SDK being used supports direct binary/multimodal attachments, this
    can be adapted to use that API.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return {"error": "Gemini API key not configured"}

    try:
        b64 = base64.b64encode(audio_bytes).decode("ascii")
        prompt = (
            "You are a multimodal assistant. A client uploaded an audio file encoded in base64. "
            "Provide ONLY a short summary (1-2 sentences) of the audio content. Do not include any extra text.\n"
            "Base64 audio:\n" + b64
        )

        import google.generativeai as genai

        genai.configure(api_key=api_key)

        def call_model():
            # Try generate_text (may accept long text) as fallback for base64 approach
            try:
                resp = genai.generate_text(model="gemini-1.5-flash", input=prompt)
                if hasattr(resp, "text") and resp.text:
                    return resp.text
                if hasattr(resp, "content") and resp.content:
                    return resp.content
                return str(resp)
            except Exception:
                # fallback to chat
                resp = genai.chat.create(model="gemini-1.5-flash", messages=[{"role": "user", "content": prompt}])
                if hasattr(resp, "candidates") and resp.candidates:
                    return getattr(resp.candidates[0], "content", str(resp))
                return str(resp)

        raw = await run_in_threadpool(call_model)
        summary = raw.strip() if isinstance(raw, str) else str(raw)
        return summary
    except Exception as exc:
        logger.exception("Gemini audio summarization failed: %s", exc)
        return {"error": f"Gemini audio summarization failed: {exc}"}


"""Service to call Google Gemini (via google-generativeai SDK) and return structured JSON.

This module prepares a prompt that instructs Gemini to return ONLY a JSON object
with the requested fields. The output is parsed with a conservative parser to
avoid crashes if Gemini includes extra text.
"""
import logging
from typing import Any, Dict
from starlette.concurrency import run_in_threadpool

from app.config.settings import settings
from app.utils.parser import safe_parse_json

logger = logging.getLogger(__name__)


async def analyze_text(conversation: str) -> Dict[str, Any]:
    """Send conversation to Gemini model and return parsed JSON with insights.

    Returns a dict with keys: summary, detected_languages, sentiment, primary_intents, topics_entities
    On failure returns reasonable defaults.
    """
    if not conversation:
        return {
            "summary": "",
            "detected_languages": [],
            "sentiment": "Neutral",
            "primary_intents": [],
            "topics_entities": [],
        }

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("GEMINI_API_KEY not configured; returning mock analysis")
        # Return a small mock response so the backend remains usable without a key
        return {
            "summary": (conversation[:300] + "...") if len(conversation) > 300 else conversation,
            "detected_languages": ["en"],
            "sentiment": "Neutral",
            "primary_intents": [],
            "topics_entities": [],
        }

    # Build the prompt instructing Gemini to output only JSON
    prompt = (
        "You are a conversation analysis engine. Return ONLY a valid JSON object with the following keys:"
        " summary, detected_languages (list), sentiment (Positive/Neutral/Negative), primary_intents (list),"
        " topics_entities (list). Do not include any explanation or extra text. Analyze the following conversation:\n\n"
        + conversation
    )

    try:
        # Use google-generativeai SDK. The call below runs in a threadpool because the
        # SDK client is synchronous.
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        def call_model():
            # generate_text or generate may differ depending on SDK version; modern versions
            # expose `generate_text` which returns an object with `text` or `content`.
            try:
                resp = genai.generate_text(model="gemini-1.5-flash", input=prompt)
                # Try to extract text safely from response
                if hasattr(resp, "text"):
                    return resp.text
                if hasattr(resp, "content"):
                    return resp.content
                # fallback to string representation
                return str(resp)
            except Exception as e:
                # Some SDKs provide `chat` or `generate` APIs; try `chat` as fallback
                try:
                    resp = genai.chat.create(model="gemini-1.5-flash", messages=[{"role": "user", "content": prompt}])
                    # depending on sdk, messages may be nested
                    if isinstance(resp, dict):
                        # try common paths
                        return resp.get("content") or resp.get("text") or str(resp)
                    return str(resp)
                except Exception:
                    raise e

        raw = await run_in_threadpool(call_model)

        # Parse the JSON portion of the model output
        parsed = safe_parse_json(raw)

        # Ensure keys exist with safe defaults
        return {
            "summary": parsed.get("summary", "") if isinstance(parsed, dict) else "",
            "detected_languages": parsed.get("detected_languages", []) if isinstance(parsed, dict) else [],
            "sentiment": parsed.get("sentiment", "Neutral") if isinstance(parsed, dict) else "Neutral",
            "primary_intents": parsed.get("primary_intents", []) if isinstance(parsed, dict) else [],
            "topics_entities": parsed.get("topics_entities", []) if isinstance(parsed, dict) else [],
        }
    except Exception as exc:
        logger.exception("Failed to call Gemini: %s", exc)
        # Return fallback minimal structure on error
        return {
            "summary": (conversation[:300] + "...") if len(conversation) > 300 else conversation,
            "detected_languages": [],
            "sentiment": "Neutral",
            "primary_intents": [],
            "topics_entities": [],
        }

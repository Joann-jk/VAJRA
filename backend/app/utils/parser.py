"""Helpers for safely parsing model output into JSON.

Gemini sometimes returns text that contains JSON embedded in prose. The helpers
here extract the first JSON object or array from a string and try to coerce it
into valid JSON, with defensive fallbacks.
"""
import json
import re
from typing import Any, Optional


def _first_json_like_segment(text: str) -> Optional[str]:
    """Find first curly-brace or square-bracket JSON-like segment in text."""
    # Search for {...} or [...] blocks
    # This is a heuristic: find the first '{' and the matching '}' (or '[' and matching ']')
    for opener, closer in [("{", "}"), ("[", "]")]:
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return None


def _cleanup_common_issues(s: str) -> str:
    """Try to fix a few common non-JSON formatting issues.

    - Replace single quotes with double quotes when safe
    - Remove trailing commas before } or ]
    - Trim leading/trailing whitespace
    """
    out = s.strip()

    # Remove trailing commas before object/array close
    out = re.sub(r",\s*([}\]])", r"\1", out)

    # Attempt to normalize single quotes to double quotes when it looks like JSON with keys
    # This is heuristic and will be tried inside a try/except when loading JSON.
    return out


def safe_parse_json(text: str) -> Any:
    """Attempt to extract and parse the first JSON object/array from text.

    Raises ValueError if parsing fails.
    """
    if not text or not isinstance(text, str):
        raise ValueError("No text to parse")

    segment = _first_json_like_segment(text)
    if not segment:
        # As a last resort, try the whole text
        segment = text

    cleaned = _cleanup_common_issues(segment)

    # Try strict JSON load first
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Try converting single quotes to double quotes heuristically
    try:
        converted = cleaned.replace("\'", '"')
        return json.loads(converted)
    except Exception as exc:
        raise ValueError(f"Failed to parse JSON from model output: {exc}\nOriginal segment: {segment}")

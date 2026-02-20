"""Simple risk engine that detects keywords and computes a score.

This is intentionally simple for hackathon/demo purposes.
"""
from typing import Dict, Any, List


async def analyze_risk(conversation: str, config: Dict[str, Any], sentiment: str) -> Dict[str, Any]:
    """Analyze a conversation for configured risk keywords and return a small risk report.

    Args:
        conversation: text to analyze
        config: dict with domain, risk_keywords, policies
        sentiment: sentiment string from model (e.g., 'Positive', 'Negative', 'Neutral')

    Returns:
        dict with keys: risk_detected (bool), trigger_keywords (list), risk_score (float), call_outcome (str)
    """
    if not conversation:
        conversation = ""

    keywords: List[str] = config.get("risk_keywords", []) or []
    lowered = conversation.lower()
    trigger_keywords = [k for k in keywords if k and k.lower() in lowered]

    risk_detected = len(trigger_keywords) > 0

    # Simple score: fraction of configured keywords that appeared, clipped to [0,1]
    denom = max(1, len(keywords))
    score = min(1.0, len(trigger_keywords) / denom)

    # Boost score slightly if sentiment is negative
    sentiment_lower = (sentiment or "").lower()
    if "neg" in sentiment_lower:
        score = min(1.0, score + 0.15)

    # Decide call outcome based on sentiment
    if "neg" in sentiment_lower:
        call_outcome = "Escalated"
    elif "pos" in sentiment_lower:
        call_outcome = "Resolved"
    else:
        call_outcome = "Neutral"

    return {
        "risk_detected": risk_detected,
        "trigger_keywords": trigger_keywords,
        "risk_score": round(float(score), 3),
        "call_outcome": call_outcome,
    }

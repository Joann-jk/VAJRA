"""API routes for the Multimodal Conversation Intelligence Backend.

Endpoint(s):
  POST /analyze - analyze text or audio conversations

Example curl (JSON):

  curl -X POST http://localhost:8000/analyze \
    -H "Content-Type: application/json" \
    -d '{"input_type":"text","conversation":"Hello world","client_config":{"domain":"sales","risk_keywords":["fraud","cancel"],"policies":["policy1"]}}'

Example curl (form + file):

  curl -X POST http://localhost:8000/analyze \
    -F "input_type=audio" \
    -F "conversation=Transcript text here" \
    -F "client_config={\"domain\":\"support\",\"risk_keywords\":[\"stop\"],\"policies\":[\"p1\"]}" \
    -F "file=@/path/to/audio.wav"

"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import AnalyzeRequest, AnalyzeResponse, ClientConfig
from app.services import gemini_service, risk_engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: Request, file: Optional[UploadFile] = File(None)):
    """Analyze a conversation.

    Accepts either JSON body or multipart/form-data (form fields + optional audio file).
    The `client_config` field should be JSON (object) when sent as a form field.
    """
    # Support both JSON and form submissions
    content_type = request.headers.get("content-type", "")
    payload = None

    if content_type.startswith("application/json"):
        payload = await request.json()
    else:
        form = await request.form()
        input_type = form.get("input_type")
        conversation = form.get("conversation")
        client_config_raw = form.get("client_config")

        if client_config_raw:
            try:
                client_config_obj = json.loads(client_config_raw)
            except Exception:
                raise HTTPException(400, "client_config must be valid JSON when sent via form field")
        else:
            client_config_obj = {}

        payload = {
            "input_type": input_type,
            "conversation": conversation,
            "client_config": client_config_obj,
        }

    # Validate payload with Pydantic
    try:
        req = AnalyzeRequest.parse_obj(payload)
    except Exception as exc:
        logger.exception("Invalid request payload: %s", exc)
        raise HTTPException(status_code=400, detail=f"Invalid request payload: {exc}")

    # If audio input_type is used, ensure conversation is provided or file is present
    if req.input_type == "audio" and not req.conversation:
        # We do not implement transcription in this demo. Ask the client to provide a transcript.
        raise HTTPException(status_code=400, detail="For audio input_type please include a 'conversation' transcript in this API (transcription not implemented).")

    # Call Gemini service to analyze the conversation text
    gemini_result = await gemini_service.analyze_text(req.conversation or "")

    # Call risk engine
    risk_result = await risk_engine.analyze_risk(req.conversation or "", req.client_config.dict(), gemini_result.get("sentiment", "Neutral"))

    # Build response according to required format
    resp = {
        "metadata": {
            "input_type": req.input_type,
            "detected_languages": gemini_result.get("detected_languages", []),
        },
        "insights": {
            "summary": gemini_result.get("summary", ""),
            "sentiment": gemini_result.get("sentiment", ""),
            "primary_intents": gemini_result.get("primary_intents", []),
            "topics_entities": gemini_result.get("topics_entities", []),
        },
        "risk_analysis": {
            "risk_detected": bool(risk_result.get("risk_detected", False)),
            "trigger_keywords": risk_result.get("trigger_keywords", []),
        },
        "advanced_analysis": {
            "call_outcome": risk_result.get("call_outcome", ""),
            "risk_score": float(risk_result.get("risk_score", 0.0)),
        },
    }

    return JSONResponse(content=resp)

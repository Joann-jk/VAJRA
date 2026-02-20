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
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.services import gemini_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze")
async def analyze(input_type: str = Form(...), file: UploadFile = File(...)):
    """Analyze an uploaded text (.txt) or audio file and return a short summary.

    Expected multipart/form-data fields:
      - input_type: "text" or "audio"
      - file: the uploaded file (text or audio)

    Example curl (text file):

      curl -X POST http://localhost:8000/analyze \
        -F "input_type=text" \
        -F "file=@/path/to/file.txt"

    Example curl (audio file):

      curl -X POST http://localhost:8000/analyze \
        -F "input_type=audio" \
        -F "file=@/path/to/audio.wav"

    The endpoint returns JSON:
    {
      "metadata": {"input_type": "text"},
      "summary": "..."
    }
    """

    input_type = (input_type or "").lower()
    if input_type not in ("text", "audio"):
        raise HTTPException(status_code=400, detail="input_type must be 'text' or 'audio'")

    if not file:
        raise HTTPException(status_code=400, detail="file upload is required")

    # Text file handling
    if input_type == "text":
        # Validate filename and content-type where possible
        if not (file.filename and file.filename.lower().endswith(".txt")):
            raise HTTPException(status_code=400, detail="Text uploads must be .txt files")

        try:
            raw = await file.read()
            text = raw.decode("utf-8")
        except Exception as exc:
            logger.exception("Failed to read/decoding uploaded text file: %s", exc)
            raise HTTPException(status_code=400, detail="Failed to read or decode text file as UTF-8")

        # Call Gemini summarization for text
        result = await gemini_service.summarize_text(text)

        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        summary = result if isinstance(result, str) else result.get("summary", "")

    else:
        # Audio handling
        try:
            audio_bytes = await file.read()
            if not audio_bytes:
                raise ValueError("Empty audio file")
        except Exception as exc:
            logger.exception("Failed to read uploaded audio file: %s", exc)
            raise HTTPException(status_code=400, detail="Failed to read uploaded audio file")

        # Call Gemini summarization for audio
        result = await gemini_service.summarize_audio(audio_bytes)

        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        summary = result if isinstance(result, str) else result.get("summary", "")

    resp = {"metadata": {"input_type": input_type}, "summary": summary}
    return JSONResponse(content=resp)

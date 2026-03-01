"""
Simple Mic → Gemini test: no Vertex, no call. Uses Gemini REST API with GEMINI_API_KEY.
Supports multi-turn (history) and system prompt for "simulate call" (AI speaks first).
Includes example seed data (Abhinav Jain, back pain follow-up).
Vertex: uses REST API on Python 3.14 (SDK has protobuf/tp_new issue).
"""
import json
import sys
import urllib.request
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from backend.config.settings import settings
from backend.config.database import get_db
from backend.models.patient import Patient
from backend.models.consultation import Consultation
from backend.agents.prompts import DOCTOR_NOTE_PROMPT

router = APIRouter(prefix="/test", tags=["test"])


class Turn(BaseModel):
    role: str  # "user" | "model"
    text: str


class ChatMessage(BaseModel):
    message: str
    system_prompt: Optional[str] = None
    history: Optional[list[Turn]] = None


class ParseTranscriptBody(BaseModel):
    transcript: str
    patient_name: str
    consultation_summary: str
    consultation_date: Optional[str] = None  # e.g. "2025-02-26" or "2 days ago"
    use_vertex: Optional[bool] = False  # if True, use Vertex AI instead of Gemini REST


def _call_gemini(key: str, contents: list, system_instruction: Optional[str] = None) -> str:
    model = (settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.fp else str(e)
        if e.code == 400 and ("API key not valid" in err_body or "INVALID_ARGUMENT" in err_body):
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", err_body[:200])
            except Exception:
                msg = err_body[:300] if len(err_body) > 300 else err_body
            raise HTTPException(
                status_code=500,
                detail=f"Gemini API key error: {msg}. Get a key at https://aistudio.google.com/apikey and set GEMINI_API_KEY in cheese/.env",
            )
        if e.code == 429:
            raise HTTPException(
                status_code=429,
                detail="Gemini quota exceeded. In cheese/.env set GEMINI_MODEL=gemini-1.5-flash-latest or gemini-2.5-flash and restart backend. See https://ai.google.dev/gemini-api/docs/rate-limits",
            )
        raise HTTPException(status_code=min(e.code, 502), detail=err_body[:500] if err_body else str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    text = None
    for c in out.get("candidates") or []:
        for p in c.get("content", {}).get("parts") or []:
            if "text" in p:
                text = p["text"].strip()
                break
        if text is not None:
            break
    return text or ""


def _vertex_initialized():
    return bool((settings.GOOGLE_PROJECT_ID or "").strip())


def _use_vertex_rest() -> bool:
    """Use Vertex REST API instead of SDK (avoids protobuf/tp_new crash on Python 3.14)."""
    return sys.version_info >= (3, 14)


def _get_vertex_token() -> str:
    """Get OAuth2 token for Vertex (service account file or gcloud application-default login)."""
    import google.auth
    import google.auth.transport.requests

    creds_path = (settings.GOOGLE_APPLICATION_CREDENTIALS or "").strip()
    if creds_path:
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    else:
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def _call_vertex_rest(contents: list, system_instruction: Optional[str] = None) -> str:
    """Call Vertex AI generateContent via REST (works on Python 3.14)."""
    project = (settings.GOOGLE_PROJECT_ID or "").strip()
    location = (settings.GCP_LOCATION or "us-central1").strip()
    model_name = (settings.VERTEX_AI_MODEL or "gemini-2.0-flash").strip()
    model_path = f"projects/{project}/locations/{location}/publishers/google/models/{model_name}"
    url = f"https://{location}-aiplatform.googleapis.com/v1/{model_path}:generateContent"
    token = _get_vertex_token()
    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.fp else str(e)
        raise RuntimeError(err_body[:500] if err_body else str(e))
    for c in out.get("candidates") or []:
        for p in c.get("content", {}).get("parts") or []:
            if "text" in p:
                return (p["text"] or "").strip()
    return ""


def _call_vertex_generate(prompt: str) -> str:
    """One-shot Vertex generate (e.g. for parse-transcript). Uses REST on 3.14 else SDK."""
    if _use_vertex_rest():
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return _call_vertex_rest(contents, system_instruction=None)
    import vertexai
    from vertexai.generative_models import GenerativeModel

    vertexai.init(project=settings.GOOGLE_PROJECT_ID, location=settings.GCP_LOCATION)
    model_name = (settings.VERTEX_AI_MODEL or "gemini-2.0-flash").strip()
    model = GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    return (response.text or "").strip()


def _call_vertex(contents: list, system_instruction: Optional[str]) -> str:
    """Call Vertex AI Gemini with chat history. Uses REST on Python 3.14 else SDK."""
    if _use_vertex_rest():
        return _call_vertex_rest(contents, system_instruction)
    import vertexai
    from vertexai.generative_models import GenerativeModel, Content, Part

    vertexai.init(project=settings.GOOGLE_PROJECT_ID, location=settings.GCP_LOCATION)
    model_name = (settings.VERTEX_AI_MODEL or "gemini-2.0-flash").strip()
    model = GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction or "You are a helpful assistant.",
    )
    def make_part(text: str):
        if hasattr(Part, "from_text"):
            return Part.from_text(text)
        return Part(text=text)

    # contents = [{"role": "user"|"model", "parts": [{"text": "..."}]}, ...]
    history = []
    for c in contents[:-1]:
        role = c.get("role", "user")
        parts = c.get("parts") or []
        text = parts[0].get("text", "").strip() if parts and isinstance(parts[0], dict) else ""
        if text:
            history.append(Content(role=role, parts=[make_part(text)]))
    chat = model.start_chat(history=history)
    last = contents[-1] if contents else {}
    last_parts = last.get("parts") or []
    last_text = (last_parts[0].get("text", "") if last_parts and isinstance(last_parts[0], dict) else "").strip()
    if not last_text:
        return ""
    response = chat.send_message(last_text)
    return (response.text or "").strip()


@router.post("/chat")
def test_chat(body: ChatMessage):
    """Send a message to Gemini (REST API). Optional system_prompt and history for multi-turn / simulate call."""
    try:
        key = (settings.GEMINI_API_KEY or "").strip()
        if not key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY not set. Add it to cheese/.env (get one at https://aistudio.google.com/apikey)",
            )
        contents = []
        for t in body.history or []:
            text = (t.text or "").strip()
            if not text:
                continue
            role = "user" if t.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": text}]})
        message = (body.message or "").strip()
        if not message:
            return {"reply": ""}
        contents.append({"role": "user", "parts": [{"text": message}]})
        reply = _call_gemini(key, contents, body.system_prompt)
        return {"reply": reply}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {type(e).__name__}: {e}")


@router.post("/chat-vertex")
def test_chat_vertex(body: ChatMessage):
    """Same as /test/chat but uses Vertex AI (GCP project; auth via gcloud auth application-default login)."""
    try:
        if not (settings.GOOGLE_PROJECT_ID or "").strip():
            raise HTTPException(
                status_code=500,
                detail="Vertex AI not configured. Set GOOGLE_PROJECT_ID in .env and run: gcloud auth application-default login",
            )
        contents = []
        for t in body.history or []:
            text = (t.text or "").strip()
            if not text:
                continue
            role = "user" if t.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": text}]})
        message = (body.message or "").strip()
        if not message:
            return {"reply": ""}
        contents.append({"role": "user", "parts": [{"text": message}]})
        reply = _call_vertex(contents, body.system_prompt)
        return {"reply": reply}
    except HTTPException:
        raise
    except Exception as e:
        err = str(e)
        if "tp_new" in err or "Metaclass" in err:
            raise HTTPException(
                status_code=500,
                detail="Vertex AI SDK fails on this Python version. Use Python 3.11 or 3.12 to run the backend (e.g. py -3.12 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000).",
            )
        raise HTTPException(status_code=500, detail=f"Vertex error: {type(e).__name__}: {e}")


@router.post("/parse-transcript")
def parse_transcript(body: ParseTranscriptBody):
    """Turn a follow-up call transcript into a short doctor-facing note. Uses Vertex if use_vertex=True else Gemini REST."""
    try:
        date_ctx = body.consultation_date or "recent visit"
        prompt = DOCTOR_NOTE_PROMPT.format(
            patient_name=body.patient_name,
            consultation_summary=body.consultation_summary,
            consultation_date=date_ctx,
            transcript=(body.transcript or "").strip() or "(No conversation recorded.)",
        )
        if body.use_vertex and _vertex_initialized():
            doctor_note = _call_vertex_generate(prompt)
        else:
            key = (settings.GEMINI_API_KEY or "").strip()
            if not key:
                raise HTTPException(
                    status_code=500,
                    detail="Set GEMINI_API_KEY in .env for Gemini, or use Vertex (select Vertex AI, set GOOGLE_PROJECT_ID, run gcloud auth application-default login)",
                )
            contents = [{"role": "user", "parts": [{"text": prompt}]}]
            doctor_note = _call_gemini(key, contents, system_instruction=None)
        return {"doctor_summary": (doctor_note or "").strip()}
    except HTTPException:
        raise
    except Exception as e:
        err = str(e)
        if "tp_new" in err or "Metaclass" in err:
            raise HTTPException(
                status_code=500,
                detail="Vertex AI requires Python 3.11 or 3.12. Restart with: py -3.12 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000",
            )
        raise HTTPException(status_code=500, detail=f"Server error: {type(e).__name__}: {e}")


EXAMPLE_PATIENT_NAME = "Abhinav Jain"
EXAMPLE_PHONE = "+15550001234"
EXAMPLE_SUMMARY = (
    "Patient presented with back pain and was prescribed medication. "
    "This is a follow-up call 2 days post-visit to check on recovery and medication adherence."
)


@router.get("/example-data")
def get_example_data():
    """Return example patient/consultation context for simulate call or UI."""
    return {
        "patient_name": EXAMPLE_PATIENT_NAME,
        "consultation_summary": EXAMPLE_SUMMARY,
        "scenario": "Calling 2 days after visit for back pain to check up.",
    }


@router.post("/seed-example")
def seed_example_data(db: Session = Depends(get_db)):
    """Create example patient (Abhinav Jain) and one consultation (back pain, 2-day follow-up). Idempotent: re-run safe."""
    patient = db.query(Patient).filter(Patient.phone_number == EXAMPLE_PHONE).first()
    if not patient:
        patient = Patient(
            name=EXAMPLE_PATIENT_NAME,
            phone_number=EXAMPLE_PHONE,
            doctor_id="dr_123",
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
    follow_up = datetime.utcnow() + timedelta(days=1)
    consultation = (
        db.query(Consultation)
        .filter(Consultation.patient_id == patient.id, Consultation.summary_text == EXAMPLE_SUMMARY)
        .first()
    )
    if not consultation:
        consultation = Consultation(
            patient_id=patient.id,
            pdf_url="local://example-back-pain.pdf",
            summary_text=EXAMPLE_SUMMARY,
            follow_up_date=follow_up,
            status="pending",
        )
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
    return {
        "patient_id": str(patient.id),
        "patient_name": patient.name,
        "consultation_id": str(consultation.id),
        "summary": consultation.summary_text,
        "follow_up_date": consultation.follow_up_date.isoformat(),
    }

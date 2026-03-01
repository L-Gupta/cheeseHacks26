from fastapi import APIRouter, WebSocket, Request, Response
import json
import asyncio
import time
import uuid
from backend.config.settings import settings
from backend.services.gemini_service import GeminiService
from backend.agents.triage_logic import TriageAnalyzer
from backend.services.escalation_service import notify_doctor
from backend.services.session_state import session_state_store
from backend.config.database import SessionLocal
from backend.models.consultation import Consultation
from backend.models.call_log import CallLog

router = APIRouter(prefix="/twilio", tags=["twilio"])

@router.post("/twiml")
async def generate_twiml(request: Request, consultation_id: str):
    """
    Endpoint Twilio hits when the call connects.
    Returns TwiML instructing Twilio to start a WebSocket Media Stream.
    """
    wss_url = f"wss://{settings.HOST_DOMAIN}/twilio/stream/{consultation_id}"
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{wss_url}" track="both_tracks" />
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@router.websocket("/stream/{consultation_id}")
async def websocket_endpoint(websocket: WebSocket, consultation_id: str):
    """
    WebSocket endpoint handling the Twilio bidirectional audio stream.
    Receives base64 encoded audio from Twilio -> sends to Google STT -> Agent -> Google TTS -> sends generated base64 audio to Twilio.
    """
    await websocket.accept()
    print(f"WebSocket connection opened for consultation: {consultation_id}")
    
    stream_sid = None
    conversation_id = str(uuid.uuid4())
    call_status = "started"
    call_started_at = time.monotonic()
    call_log_id = None

    session_state_store.start(conversation_id=conversation_id, consultation_id=str(consultation_id))

    def _load_consultation(db):
        try:
            consultation_uuid = uuid.UUID(consultation_id)
        except ValueError:
            consultation_uuid = None
        if consultation_uuid is not None:
            return db.query(Consultation).filter(Consultation.id == consultation_uuid).first(), consultation_uuid
        return db.query(Consultation).filter(Consultation.id == consultation_id).first(), consultation_uuid

    db = SessionLocal()
    try:
        consultation, consultation_uuid = _load_consultation(db)
        draft_log = CallLog(
            conversation_id=conversation_id,
            consultation_id=consultation.id if consultation else consultation_uuid,
            transcript="",
            ai_summary="",
            urgency_level="low",
            call_duration=0,
            call_status=call_status,
            dashboard_alert=False,
        )
        db.add(draft_log)
        db.commit()
        db.refresh(draft_log)
        call_log_id = draft_log.id
    except Exception as e:
        print(f"Failed to create draft call log for consultation {consultation_id}: {e}")
        db.rollback()
    finally:
        db.close()

    async def persist_transcript_checkpoint(transcript: str):
        session_state_store.update_transcript(conversation_id, transcript)
        if not call_log_id:
            return
        db_local = SessionLocal()
        try:
            log = db_local.query(CallLog).filter(CallLog.id == call_log_id).first()
            if log:
                log.transcript = transcript
                log.call_duration = int(max(0, time.monotonic() - call_started_at))
                db_local.commit()
        except Exception as e:
            db_local.rollback()
            print(f"Failed to persist transcript checkpoint for call {conversation_id}: {e}")
        finally:
            db_local.close()
    
    # Initialize our AI agent which encapsulates Vertex AI, Google STT, and Google TTS
    agent = GeminiService(consultation_id=consultation_id, on_transcript_update=persist_transcript_checkpoint)
    try:
        await agent.initialize()
    except Exception as e:
        print(f"Agent initialization failed for consultation {consultation_id}: {e}")
        call_status = "failed"
        session_state_store.end(conversation_id)
        session_state_store.cleanup(conversation_id)
        try:
            await websocket.close()
        except Exception:
            pass
        return

    # Task to read audio from Agent's TTS and forward to Twilio
    async def send_to_twilio():
        async for tts_chunk in agent.get_audio_chunks():
            if stream_sid:
                media_message = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": tts_chunk
                    }
                }
                await websocket.send_json(media_message)

    sender_task = asyncio.create_task(send_to_twilio())

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            event_type = data.get("event", "")
            seq = str(data.get("sequenceNumber", ""))
            media_fallback = ""
            if event_type == "media" and not seq:
                media_fallback = str(data.get("media", {}).get("timestamp", "")) or str(hash(data.get("media", {}).get("payload", "")))
            event_key = f"{stream_sid or 'nostream'}:{event_type}:{seq or media_fallback}"
            if not session_state_store.mark_event_processed(conversation_id, event_key):
                continue

            if event_type == 'start':
                stream_sid = data['start']['streamSid']
                session_state_store.update_stream_sid(conversation_id, stream_sid)
                print(f"Stream started: {stream_sid}")
                # Tell Agent to speak the greeting
                await agent.start_conversation()

            elif event_type == 'media':
                # Incoming audio payload from Twilio (mulaw 8000Hz base64)
                payload = data['media']['payload']
                # Feed the raw payload to the Agent's STT processor
                await agent.process_incoming_audio(payload)
                if agent.should_end_conversation():
                    call_status = "completed"
                    break

            elif event_type == 'stop':
                print(f"Stream stopped: {stream_sid}")
                call_status = "completed"
                break

    except Exception as e:
        print(f"WebSocket disconnected: {e}")
        call_status = "failed"
    finally:
        session_state_store.end(conversation_id)
        sender_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass
        await agent.close()

        transcript = agent.get_transcript()

        try:
            triage_result = TriageAnalyzer().analyze_call(transcript)
        except Exception as e:
            print(f"Triage failed for consultation {consultation_id}: {e}")
            triage_result = {
                "summary": "Triage analysis failed.",
                "urgency": "high",
                "requires_doctor": True
            }

        requires_doctor = agent.should_force_escalation() or bool(triage_result.get("requires_doctor", False))
        urgency = str(triage_result.get("urgency", "low")).lower()
        if urgency not in {"low", "medium", "high"}:
            urgency = "medium"
        if urgency == "high":
            requires_doctor = True
        new_status = "escalated" if urgency == "high" else "completed"
        dashboard_alert = urgency in {"medium", "high"}
        call_duration = int(max(0, time.monotonic() - call_started_at))

        db = SessionLocal()
        try:
            consultation, consultation_uuid = _load_consultation(db)

            if consultation:
                consultation.status = new_status

            if call_log_id:
                call_log = db.query(CallLog).filter(CallLog.id == call_log_id).first()
            else:
                call_log = None
            if not call_log:
                call_log = CallLog(
                    conversation_id=conversation_id,
                    consultation_id=consultation.id if consultation else consultation_uuid,
                )
                db.add(call_log)

            call_log.transcript = transcript
            call_log.ai_summary = triage_result.get("summary", "")
            call_log.urgency_level = urgency
            call_log.call_duration = call_duration
            call_log.call_status = call_status
            call_log.dashboard_alert = dashboard_alert

            if urgency == "high" and requires_doctor:
                doctor_phone_number = getattr(getattr(consultation, "patient", None), "doctor_id", None)
                notify_doctor(
                    consultation_id=consultation_id,
                    summary=triage_result.get("summary", ""),
                    urgency=urgency,
                    doctor_phone_number=doctor_phone_number
                )

            db.commit()
        except Exception as e:
            print(f"Failed to finalize call for consultation {consultation_id}: {e}")
            db.rollback()
        finally:
            db.close()
            session_state_store.cleanup(conversation_id)

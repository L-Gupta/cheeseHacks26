from fastapi import APIRouter, WebSocket, Request, Response
import json
import asyncio
import time
import uuid
from backend.config.settings import settings
from backend.services.gemini_service import GeminiService
from backend.agents.triage_logic import TriageAnalyzer
from backend.services.escalation_service import notify_doctor
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
    call_status = "started"
    call_started_at = time.monotonic()
    
    # Initialize our AI agent which encapsulates Vertex AI, Google STT, and Google TTS
    agent = GeminiService(consultation_id=consultation_id)
    await agent.initialize()

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

            if data['event'] == 'start':
                stream_sid = data['start']['streamSid']
                print(f"Stream started: {stream_sid}")
                # Tell Agent to speak the greeting
                await agent.start_conversation()

            elif data['event'] == 'media':
                # Incoming audio payload from Twilio (mulaw 8000Hz base64)
                payload = data['media']['payload']
                # Feed the raw payload to the Agent's STT processor
                await agent.process_incoming_audio(payload)
                if agent.should_end_conversation():
                    call_status = "completed"
                    break

            elif data['event'] == 'stop':
                print(f"Stream stopped: {stream_sid}")
                call_status = "completed"
                break

    except Exception as e:
        print(f"WebSocket disconnected: {e}")
        call_status = "failed"
    finally:
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
        new_status = "escalated" if requires_doctor else "completed"
        call_duration = int(max(0, time.monotonic() - call_started_at))

        db = SessionLocal()
        try:
            try:
                consultation_uuid = uuid.UUID(consultation_id)
            except ValueError:
                consultation_uuid = None

            if consultation_uuid is not None:
                consultation = db.query(Consultation).filter(Consultation.id == consultation_uuid).first()
            else:
                consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()

            if consultation:
                consultation.status = new_status

            call_log = CallLog(
                consultation_id=consultation.id if consultation else consultation_uuid,
                transcript=transcript,
                ai_summary=triage_result.get("summary", ""),
                urgency_level=triage_result.get("urgency", "low"),
                call_duration=call_duration,
                call_status=call_status
            )
            db.add(call_log)

            if requires_doctor:
                notify_doctor(
                    consultation_id=consultation_id,
                    summary=triage_result.get("summary", ""),
                    urgency=triage_result.get("urgency", "high")
                )

            db.commit()
        except Exception as e:
            print(f"Failed to finalize call for consultation {consultation_id}: {e}")
            db.rollback()
        finally:
            db.close()

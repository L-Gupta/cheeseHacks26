from fastapi import APIRouter, WebSocket, Request, Response
import json
import asyncio
from backend.config.settings import settings
from backend.services.gemini_service import GeminiService

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

            elif data['event'] == 'stop':
                print(f"Stream stopped: {stream_sid}")
                break

    except Exception as e:
        print(f"WebSocket disconnected: {e}")
    finally:
        sender_task.cancel()
        await agent.close()
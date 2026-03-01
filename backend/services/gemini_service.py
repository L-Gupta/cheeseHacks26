import asyncio
# import json, urllib.request  # for Gemini REST path (commented out)
from backend.config.settings import settings
from backend.agents.prompts import get_system_prompt
from backend.services.pinecone_service import PineconeService
from backend.services.speech_to_text import STTService
from backend.services.text_to_speech import TTSService
from backend.config.database import SessionLocal
from backend.models.consultation import Consultation
from backend.models.patient import Patient


# def _gemini_rest_chat(key: str, contents: list, system_instruction: str) -> str:
#     """Call Gemini REST API (generativelanguage.googleapis.com). Used when not using Vertex."""
#     model = (settings.GEMINI_MODEL or "gemini-1.5-flash-latest").strip()
#     url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
#     payload = {
#         "contents": contents,
#         "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
#     }
#     if system_instruction:
#         payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
#     data = json.dumps(payload).encode("utf-8")
#     req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
#     with urllib.request.urlopen(req, timeout=30) as resp:
#         out = json.loads(resp.read().decode())
#     for c in out.get("candidates") or []:
#         for p in c.get("content", {}).get("parts") or []:
#             if "text" in p:
#                 return (p["text"] or "").strip()
#     return ""


class GeminiService:
    def __init__(self, consultation_id: str):
        self.consultation_id = consultation_id
        self.patient_name = "Patient"
        self.consultation_summary = "General follow-up."
        
        # Audio handling sub-services (Google Cloud native)
        self.stt = STTService(callback=self._on_patient_speaking)
        self.tts = TTSService()
        self.audio_out_queue = asyncio.Queue()
        self.chat = None
        # self._gemini_history = []  # for Gemini REST path (commented out)
        # self._system_prompt = ""

    async def initialize(self):
        """Fetch RAG context, init LLM (Vertex or Gemini REST), start STT."""
        pinecone_db = PineconeService()
        metadata = pinecone_db.query_context(self.consultation_id)
        
        if metadata and "summary_text" in metadata:
             self.consultation_summary = metadata["summary_text"]
             
        db = SessionLocal()
        try:
            consultation = db.query(Consultation).filter(Consultation.id == self.consultation_id).first()
            if consultation and consultation.patient:
                self.patient_name = consultation.patient.name
        except Exception as e:
            print(f"Error fetching DB patient: {e}")
        finally:
            db.close()

        # Same script as before: Emily call flow (positive / negative path, transcript, severity, goodbye)
        system_prompt_parts = get_system_prompt(self.patient_name, self.consultation_summary)
        system_instruction = "\n".join(system_prompt_parts) if isinstance(system_prompt_parts, list) else system_prompt_parts

        if not (settings.GOOGLE_PROJECT_ID or "").strip():
            raise RuntimeError(
                "Vertex required for real calls. Set GOOGLE_PROJECT_ID in .env and run: gcloud auth application-default login"
            )
        import vertexai
        from vertexai.generative_models import GenerativeModel
        vertexai.init(project=settings.GOOGLE_PROJECT_ID, location=settings.GCP_LOCATION)
        model = GenerativeModel(
            model_name=settings.VERTEX_AI_MODEL,
            system_instruction=system_instruction,
        )
        self.chat = model.start_chat()

        # Start Google Speech-to-Text streaming
        await self.stt.initialize()

    async def start_conversation(self):
        """Initiate the call with a synthesized greeting from Google TTS."""
        greeting = f"Hi {self.patient_name}, this is Emily calling from the clinic to see how you're feeling since your last visit. Is now a good time to talk?"
        print("Gemini Agent Speaking:", greeting)
        
        async for chunk in self.tts.synthesize(greeting):
            await self.audio_out_queue.put(chunk)

    async def process_incoming_audio(self, mulaw_b64: str):
        """Receive Twilio audio via WebSocket and funnel it to Google STT"""
        await self.stt.capture_input(mulaw_b64)

    async def _on_patient_speaking(self, text: str):
        """Callback from Google STT when the patient finishes a sentence."""
        print("Patient Said:", text)
        try:
            response = self.chat.send_message(text)
            ai_text = response.text
            print("Gemini Agent Replying:", ai_text)
            async for chunk in self.tts.synthesize(ai_text):
                await self.audio_out_queue.put(chunk)
        except Exception as e:
            print(f"Vertex AI (Gemini) Error: {e}")

    async def get_audio_chunks(self):
        """Generator to drain audio out queue to Twilio WebSockets."""
        while True:
            chunk = await self.audio_out_queue.get()
            if chunk is None:
                break
            yield chunk

    async def close(self):
        """Cleanup Streams."""
        await self.stt.close()
        await self.audio_out_queue.put(None)

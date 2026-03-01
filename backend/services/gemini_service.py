import asyncio
import re
import uuid
import vertexai
from vertexai.generative_models import GenerativeModel
from backend.config.settings import settings
from backend.agents.prompts import get_system_prompt
from backend.services.embedding_service import EmbeddingService
from backend.services.pinecone_service import PineconeService
from backend.services.speech_to_text import STTService
from backend.services.text_to_speech import TTSService
from backend.config.database import SessionLocal
from backend.models.consultation import Consultation
from backend.models.patient import Patient

class GeminiService:
    def __init__(self, consultation_id: str, on_transcript_update=None):
        self.consultation_id = consultation_id
        self.patient_name = "Patient"
        self.consultation_summary = "General follow-up."
        self.transcript_lines: list[str] = []
        self.end_requested = False
        self.force_escalation = False
        self.on_transcript_update = on_transcript_update
        self.empty_turns = 0
        
        # Audio handling sub-services (Google Cloud native)
        self.stt = STTService(callback=self._on_patient_speaking)
        self.tts = TTSService()
        self.audio_out_queue = asyncio.Queue()
        self.chat = None

    async def initialize(self):
        """Fetch RAG context from Pinecone, initialize Vertex AI, start Google STT listening loops."""
        db = SessionLocal()
        consultation = None
        try:
            try:
                consultation_key = uuid.UUID(str(self.consultation_id))
            except ValueError:
                consultation_key = self.consultation_id

            consultation = db.query(Consultation).filter(Consultation.id == consultation_key).first()
            if consultation and consultation.patient:
                self.patient_name = consultation.patient.name
                self.consultation_summary = consultation.summary_text or self.consultation_summary
        except Exception as e:
            print(f"Error fetching DB patient: {e}")
        finally:
            db.close()

        rag_context = ""
        try:
            pinecone_db = PineconeService()
            embedder = EmbeddingService()
            query_vector = embedder.generate_embedding(self.consultation_summary)
            top_matches = pinecone_db.query_similar_chunks(
                query_vector=query_vector,
                consultation_id=str(consultation.id) if consultation else None,
                top_k=3,
            )
            rag_context = " ".join([m.get("summary_text", "") for m in top_matches if m.get("summary_text")]).strip()
        except Exception as e:
            print(f"RAG context lookup failed: {e}")

        # Vertex AI SDK (gemini-2.5-flash)
        vertexai.init(project=settings.GOOGLE_PROJECT_ID, location=settings.GCP_LOCATION)
        model = GenerativeModel(
            model_name=settings.VERTEX_AI_MODEL,
            system_instruction=get_system_prompt(self.patient_name, self.consultation_summary, rag_context=rag_context)
        )
        self.chat = model.start_chat()
        
        # Start Google Speech-to-Text streaming
        await self.stt.initialize()

    async def start_conversation(self):
        """Initiate the call with a synthesized greeting from Google TTS."""
        greeting = f"Hi {self.patient_name}, this is Emily calling from the clinic to see how you're feeling since your last visit. Is now a good time to talk?"
        print("Gemini Agent Speaking:", greeting)
        await self._append_transcript_line(f"AI: {greeting}")
        
        async for chunk in self.tts.synthesize(greeting):
            await self.audio_out_queue.put(chunk)

    async def process_incoming_audio(self, mulaw_b64: str):
        """Receive Twilio audio via WebSocket and funnel it to Google STT"""
        await self.stt.capture_input(mulaw_b64)

    async def _on_patient_speaking(self, text: str):
        """Callback from Google STT when the patient finishes a sentence."""
        if self.end_requested:
            return

        if not (text or "").strip():
            self.empty_turns += 1
            if self.empty_turns <= 2:
                reprompt = "I could not hear you clearly. Could you please repeat that?"
                await self._append_transcript_line(f"AI: {reprompt}")
                async for chunk in self.tts.synthesize(reprompt):
                    await self.audio_out_queue.put(chunk)
                return

            ai_text = "I am still unable to hear you. We will follow up again soon. Goodbye."
            self.force_escalation = True
            self.end_requested = True
            await self._append_transcript_line(f"AI: {ai_text}")
            async for chunk in self.tts.synthesize(ai_text):
                await self.audio_out_queue.put(chunk)
            return

        self.empty_turns = 0
        print("Patient Said:", text)
        await self._append_transcript_line(f"Patient: {text}")

        lower = text.lower()
        ok_patterns = [
            r"\bi('m| am)?\s*(ok|okay|fine|good|better)\b",
            r"\bno (new )?(symptoms|issues|problems)\b",
            r"\bfeeling (better|good|fine)\b",
        ]
        problem_patterns = [
            r"\b(pain|worse|problem|issue|symptom|nausea|dizzy|bleeding|fever|doctor)\b",
            r"\bnot (better|good|fine|okay)\b",
        ]

        if any(re.search(p, lower) for p in ok_patterns):
            ai_text = "Glad to hear you're feeling okay. Thank you for your time. Goodbye."
            print("Gemini Agent Replying:", ai_text)
            await self._append_transcript_line(f"AI: {ai_text}")
            self.end_requested = True
            async for chunk in self.tts.synthesize(ai_text):
                await self.audio_out_queue.put(chunk)
            return

        if any(re.search(p, lower) for p in problem_patterns):
            ai_text = "Thank you for sharing that. I will alert your doctor right away. Goodbye."
            print("Gemini Agent Replying:", ai_text)
            await self._append_transcript_line(f"AI: {ai_text}")
            self.force_escalation = True
            self.end_requested = True
            async for chunk in self.tts.synthesize(ai_text):
                await self.audio_out_queue.put(chunk)
            return

        try:
            response = await asyncio.wait_for(asyncio.to_thread(self.chat.send_message, text), timeout=20)
            ai_text = response.text
            print("Gemini Agent Replying:", ai_text)
            await self._append_transcript_line(f"AI: {ai_text}")
            if "goodbye" in ai_text.lower():
                self.end_requested = True
            
            # Send the LLM output back to TTS
            async for chunk in self.tts.synthesize(ai_text):
                await self.audio_out_queue.put(chunk)
        except asyncio.TimeoutError:
            ai_text = "I am having trouble processing right now. I will notify your doctor to follow up. Goodbye."
            self.force_escalation = True
            self.end_requested = True
            await self._append_transcript_line(f"AI: {ai_text}")
            async for chunk in self.tts.synthesize(ai_text):
                await self.audio_out_queue.put(chunk)
        except Exception as e:
            print(f"Vertex AI (Gemini) Error: {e}")
            ai_text = "I am having technical trouble. Your doctor will follow up soon. Goodbye."
            self.force_escalation = True
            self.end_requested = True
            await self._append_transcript_line(f"AI: {ai_text}")
            async for chunk in self.tts.synthesize(ai_text):
                await self.audio_out_queue.put(chunk)

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

    def get_transcript(self) -> str:
        """Returns full call transcript collected from patient and AI turns."""
        return "\n".join(self.transcript_lines).strip()

    def should_end_conversation(self) -> bool:
        return self.end_requested

    def should_force_escalation(self) -> bool:
        return self.force_escalation

    async def _append_transcript_line(self, line: str) -> None:
        self.transcript_lines.append(line)
        if self.on_transcript_update:
            try:
                await self.on_transcript_update(self.get_transcript())
            except Exception as e:
                print(f"Transcript checkpoint failed: {e}")

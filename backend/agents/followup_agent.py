import asyncio
import vertexai
from vertexai.generative_models import GenerativeModel
from backend.config.settings import settings
from backend.agents.prompts import get_system_prompt
from backend.services.pinecone_service import PineconeService
from backend.services.stt_service import STTService
from backend.services.tts_service import TTSService
from backend.config.database import SessionLocal
from backend.models.consultation import Consultation
from backend.models.patient import Patient

class AI_FollowUp_Agent:
    def __init__(self, consultation_id: str):
        self.consultation_id = consultation_id
        self.patient_name = "Patient"
        self.consultation_summary = "General follow-up."
        
        # Audio handling sub-services
        self.stt = STTService(callback=self._on_patient_speaking)
        self.tts = TTSService()
        self.audio_out_queue = asyncio.Queue()
        self.chat = None

    async def initialize(self):
        """Fetch RAG context, initialize Vertex AI, and start STT listening loops"""
        # Fetch Context
        pinecone_db = PineconeService()
        metadata = pinecone_db.query_context(self.consultation_id)
        
        if metadata and "summary_text" in metadata:
             self.consultation_summary = metadata["summary_text"]
             
        # Optional: fetch accurate patient name from Cloud SQL
        db = SessionLocal()
        try:
            consultation = db.query(Consultation).filter(Consultation.id == self.consultation_id).first()
            if consultation and consultation.patient:
                self.patient_name = consultation.patient.name
        except Exception as e:
            print(f"Error fetching DB patient: {e}")
        finally:
            db.close()

        # Initialize Vertex AI SDK
        vertexai.init(project=settings.GOOGLE_PROJECT_ID, location=settings.GCP_LOCATION)
        model = GenerativeModel(
            model_name=settings.VERTEX_AI_MODEL,
            system_instruction=get_system_prompt(self.patient_name, self.consultation_summary)
        )
        self.chat = model.start_chat()
        
        # Start Deepgram WebSocket listener
        await self.stt.initialize()

    async def start_conversation(self):
        """Initiate the call with a greeting"""
        greeting = f"Hi {self.patient_name}, this is Emily calling from the clinic to see how you're feeling since your last visit. Is now a good time to talk?"
        print("Agent Speaking:", greeting)
        
        async for chunk in self.tts.synthesize(greeting):
            await self.audio_out_queue.put(chunk)

    async def process_incoming_audio(self, mulaw_b64: str):
        """Receive Twilio audio and funnel it to Deepgram STT"""
        await self.stt.capture_input(mulaw_b64)

    async def _on_patient_speaking(self, text: str):
        """Callback from Deepgram STT when the patient finishes a sentence"""
        print("Patient Said:", text)
        try:
            response = self.chat.send_message(text)
            ai_text = response.text
            print("Agent Replying:", ai_text)
            
            async for chunk in self.tts.synthesize(ai_text):
                await self.audio_out_queue.put(chunk)
        except Exception as e:
            print(f"Vertex AI Error: {e}")

    async def get_audio_chunks(self):
        """Generator pulled by the WebSocket route to send to Twilio"""
        while True:
            chunk = await self.audio_out_queue.get()
            if chunk is None:
                break
            yield chunk

    async def close(self):
        """Cleanup streams and save summary"""
        await self.stt.close()
        await self.audio_out_queue.put(None)
        
        # You would invoke `TriageAnalyzer` here
        # db = SessionLocal(); triage = TriageAnalyzer(); db.add(CallLog(...)); db.commit();

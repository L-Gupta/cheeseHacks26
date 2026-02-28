from vertexai.generative_models import GenerativeModel, Content, Part
import vertexai
from backend.config.settings import settings
import asyncio

class AI_FollowUp_Agent:
    def __init__(self, consultation_id: int):
        self.consultation_id = consultation_id
        
        # We need the consultation model to build the prompt context
        self.consultation_summary = "Patient visited for follow-up on hypertension." # Mocked until DB inject
        self.patient_name = "Yash" # Mocked until DB inject
        
        # Initialize Vertex AI SDK
        vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION)
        self.model = GenerativeModel(
            model_name=settings.VERTEX_AI_MODEL,
            system_instruction=[
                "You are Emily, a friendly and empathetic AI medical assistant calling on behalf of the clinic.",
                f"You are speaking to {self.patient_name}.",
                f"The consultation summary is: {self.consultation_summary}",
                "Your job is to check on the patient, ask how they are feeling, and if they have adhered to any medication.",
                "Keep responses extremely brief (1-2 sentences max) as this is a spoken phone conversation.",
                "Do not use markdown, emojis, or bullet points.",
                "Always end your turn with a question to prompt the patient."
            ]
        )
        self.chat = self.model.start_chat()
        
        # Audio handling sub-services
        # Assuming we import from the same path
        from backend.services.stt_service import STTService
        from backend.services.tts_service import TTSService
        self.stt = STTService(callback=self._on_patient_speaking)
        self.tts = TTSService()
        
        # Queue for generated audio chunks to stream back out
        self.audio_out_queue = asyncio.Queue()

    async def initialize(self):
        """Start STT listening loops"""
        await self.stt.initialize()

    async def start_conversation(self):
        """Initiate the call with a greeting"""
        greeting = f"Hi {self.patient_name}, this is Emily calling from the clinic to see how you're feeling since your last visit. Is now a good time to talk?"
        print("Agent Speaking:", greeting)
        
        # Generate TTS audio for the greeting and push it out
        async for chunk in self.tts.synthesize(greeting):
            await self.audio_out_queue.put(chunk)

    async def process_incoming_audio(self, mulaw_b64: str):
        """Receive Twilio audio and funnel it to STT"""
        await self.stt.capture_input(mulaw_b64)

    async def _on_patient_speaking(self, text: str):
        """Callback from STT when the patient finishes a sentence"""
        print("Patient Said:", text)
        
        # Send transcript to Vertex AI Gemini model
        try:
            response = self.chat.send_message(text)
            ai_text = response.text
            print("Agent Replying:", ai_text)
            
            # Synthesize response 
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
        
        # Trigger an LLM call to summarize the conversation at the end
        if self.chat.history:
             summary_prompt = "Generate a brief JSON summary of this interaction including 'summary' (string), 'urgency' (low, medium, high), and 'requires_doctor' (boolean)."
             # Try / catch omitted for brevity, but you'd save this to `backend.models.call_log`
             print("Summary logic here...")

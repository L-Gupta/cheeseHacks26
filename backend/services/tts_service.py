import base64
import asyncio
from google.cloud import texttospeech
from backend.config.settings import settings

class TTSService:
    def __init__(self):
        # We assume GOOGLE_APPLICATION_CREDENTIALS are set or ADC
        self.client = texttospeech.TextToSpeechAsyncClient()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-F", # Journey voices sound naturally conversational
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MULAW, # Twilio needs MULAW
            sample_rate_hertz=8000
        )
        
    async def synthesize(self, text: str):
        """
        Takes raw text from the AI Agent, synthesizes it using Google Cloud TTS, 
        and yields base64 encoded chunks suitable for Twilio.
        """
        request = texttospeech.SynthesizeSpeechRequest(
            input=texttospeech.SynthesisInput(text=text),
            voice=self.voice,
            audio_config=self.audio_config
        )
        
        try:
            response = await self.client.synthesize_speech(request=request)
            
            # response.audio_content is raw bytes
            # Twilio media streams expect base64 encoded chunks of mulaw bytes
            encoded_audio = base64.b64encode(response.audio_content).decode("utf-8")
            
            # Simple chunking if the response is large, otherwise yield the whole thing
            # In a real streaming implementation, you might want to chunk these bytes into 20ms frames
            # but Twilio can handle larger base64 payloads as long as they aren't huge.
            # 8000hz mulaw = 8000 bytes per second.
            chunk_size = 4000 # ~0.5 seconds of audio per chunk
            for i in range(0, len(encoded_audio), chunk_size):
                yield encoded_audio[i:i + chunk_size]
                await asyncio.sleep(0.01) # Give websocket loop time to breathe
                
        except Exception as e:
            print(f"Error in TTS synthesis: {e}")

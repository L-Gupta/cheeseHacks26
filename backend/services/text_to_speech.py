import base64
import asyncio
from google.cloud import texttospeech

class TTSService:
    def __init__(self):
        self.client = texttospeech.TextToSpeechAsyncClient()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-F", # Natural conversational voice
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MULAW,
            sample_rate_hertz=8000
        )
        
    async def synthesize(self, text: str):
        """
        Takes raw text, synthesizes it using Google Cloud TTS, 
        and yields base64 encoded chunks suitable for Twilio WebSockets.
        """
        request = texttospeech.SynthesizeSpeechRequest(
            input=texttospeech.SynthesisInput(text=text),
            voice=self.voice,
            audio_config=self.audio_config
        )
        
        try:
            response = await self.client.synthesize_speech(request=request)
            encoded_audio = base64.b64encode(response.audio_content).decode("utf-8")
            
            # Chunking 8000hz mulaw bytes (~0.5 seconds of audio per chunk)
            chunk_size = 4000 
            for i in range(0, len(encoded_audio), chunk_size):
                yield encoded_audio[i:i + chunk_size]
                await asyncio.sleep(0.01) # Yield execution back to event loop
                
        except Exception as e:
            print(f"Error in Google TTS synthesis: {e}")
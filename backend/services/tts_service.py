import httpx
import base64
import asyncio
from backend.config.settings import settings

class TTSService:
    def __init__(self):
        # Deepgram Aura TTS configuration for 8000Hz mulaw
        self.url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=mulaw&sample_rate=8000"
        self.headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        }
        
    async def synthesize(self, text: str):
        """
        Takes raw text, synthesizes using Deepgram Aura, 
        yielding base64 encoded chunks suitable for Twilio.
        """
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("POST", self.url, headers=self.headers, json={"text": text}) as response:
                    response.raise_for_status()
                    # Stream chunks as they arrive from Deepgram
                    async for chunk in response.aiter_bytes(chunk_size=4000):
                        if chunk:
                            encoded_audio = base64.b64encode(chunk).decode("utf-8")
                            yield encoded_audio
                            await asyncio.sleep(0.01) # Breathe
            except Exception as e:
                print(f"Error in Deepgram TTS synthesis: {e}")

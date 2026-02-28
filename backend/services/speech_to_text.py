import asyncio
import base64
from google.cloud import speech
from google.api_core.exceptions import OutOfRange

class STTService:
    def __init__(self, callback):
        self.callback = callback
        self.client = speech.SpeechAsyncClient()
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
            sample_rate_hertz=8000,
            language_code="en-US",
            model="phone_call", 
            use_enhanced=True
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config,
            interim_results=False
        )
        
        self.audio_queue = asyncio.Queue()
        self.stream_task = None
        self.is_running = False

    async def initialize(self):
        self.is_running = True
        self.stream_task = asyncio.create_task(self._process_stream())
        print("Initialized Google STT Stream")

    async def capture_input(self, audio_chunk_base64: str):
        """Receives base64 audio from Twilio and passes to Google STT queue."""
        if self.is_running:
            decoded_bytes = base64.b64decode(audio_chunk_base64)
            await self.audio_queue.put(decoded_bytes)

    async def _generator(self):
        """Yields audio chunks for Google's streaming GRPC client."""
        while self.is_running:
            chunk = await self.audio_queue.get()
            if chunk is None:
                return
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    async def _process_stream(self):
        try:
            requests = self._generator()
            
            responses = await self.client.streaming_recognize(
                config=self.streaming_config,
                requests=requests
            )
            
            async for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                transcript = result.alternatives[0].transcript
                if result.is_final:
                    # Pass transcribed sentence back to Agent loop
                    await self.callback(transcript.strip())
                    
        except OutOfRange:
            print("Google STT Stream timed out (5m limit). Restart required for longer calls.")
        except Exception as e:
            print(f"STT stream exception: {e}")

    async def close(self):
        self.is_running = False
        await self.audio_queue.put(None)
        if self.stream_task:
            self.stream_task.cancel()

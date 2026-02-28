import os
from google.cloud import speech
from google.api_core.exceptions import OutOfRange

class STTService:
    def __init__(self, callback):
        self.client = speech.SpeechAsyncClient()
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
            sample_rate_hertz=8000,
            language_code="en-US",
            model="phone_call", # Optimized for phone interactions
            use_enhanced=True
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config,
            interim_results=False # Set to True if you want partial interrupts
        )
        
        self.audio_queue = asyncio.Queue()
        self.callback = callback
        self.stream_task = None
        self.is_running = False

    async def initialize(self):
        self.is_running = True
        self.stream_task = asyncio.create_task(self._process_stream())

    async def add_chunk(self, chunk: bytes):
        if self.is_running:
            await self.audio_queue.put(chunk)

    async def _generator(self):
        while self.is_running:
            chunk = await self.audio_queue.get()
            if chunk is None:
                return
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    async def _process_stream(self):
        try:
            requests = self._generator()
            
            # Asynchronous streaming
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
                    # Pass the fully transcribed phrase back to the Agent
                    await self.callback(transcript)
                    
        except OutOfRange:
            # Google streaming limits out (approx 5 mins). Restart stream if needed.
            print("STT Stream timed out, restarting usually handled here.")
        except Exception as e:
            print(f"STT stream exception: {e}")

    async def capture_input(self, audio_chunk_base64: str):
        """
        Receives base64 audio from Twilio WebSocket and passes it to the queue
        """
        import base64
        # Decode base64 to byte payload
        decoded_bytes = base64.b64decode(audio_chunk_base64)
        await self.add_chunk(decoded_bytes)

    async def close(self):
        self.is_running = False
        await self.audio_queue.put(None)
        if self.stream_task:
            await self.stream_task

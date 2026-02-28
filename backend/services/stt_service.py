import websockets
import json
import asyncio
import base64
from backend.config.settings import settings

class STTService:
    def __init__(self, callback):
        self.callback = callback
        self.ws = None
        self.audio_queue = asyncio.Queue()
        self.is_running = False
        self.recv_task = None
        self.send_task = None

    async def initialize(self):
        self.is_running = True
        
        # Connect to Deepgram Nova-2 via WebSockets
        url = "wss://api.deepgram.com/v1/listen?encoding=mulaw&sample_rate=8000&channels=1&model=nova-2-phonecall&endpointing=500"
        headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
        
        try:
            self.ws = await websockets.connect(url, extra_headers=headers)
            print("Connected to Deepgram STT WebSocket")
            self.recv_task = asyncio.create_task(self._receive_loop())
            self.send_task = asyncio.create_task(self._send_loop())
        except Exception as e:
            print(f"Failed to connect to Deepgram STT: {e}")

    async def capture_input(self, audio_chunk_base64: str):
        """Receives base64 audio from Twilio and queues it for Deepgram"""
        decoded_bytes = base64.b64decode(audio_chunk_base64)
        if self.is_running:
            await self.audio_queue.put(decoded_bytes)

    async def _send_loop(self):
        """Pops raw audio bytes from queue and sends them to Deepgram"""
        try:
            while self.is_running and self.ws:
                chunk = await self.audio_queue.get()
                if chunk is None:
                     # Send CloseStream message to Deepgram
                     await self.ws.send(json.dumps({"type": "CloseStream"}))
                     break
                await self.ws.send(chunk)
        except Exception as e:
            print(f"Deepgram sending error: {e}")

    async def _receive_loop(self):
        """Listens for transcripts from Deepgram"""
        try:
            while self.is_running and self.ws:
                msg = await self.ws.recv()
                data = json.loads(msg)
                
                # Check for transcript
                if data.get("type") == "Results":
                     is_final = data.get("is_final", False)
                     alternatives = data.get("channel", {}).get("alternatives", [])
                     if alternatives:
                         transcript = alternatives[0].get("transcript", "")
                         if is_final and transcript.strip():
                             await self.callback(transcript)
        except websockets.exceptions.ConnectionClosed:
            print("Deepgram STT connection closed.")
        except Exception as e:
            print(f"Deepgram receiving error: {e}")

    async def close(self):
        self.is_running = False
        await self.audio_queue.put(None)
        if self.recv_task:
            self.recv_task.cancel()
        if self.ws:
            await self.ws.close()

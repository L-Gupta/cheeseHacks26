from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock


@dataclass
class SessionState:
    conversation_id: str
    consultation_id: str
    stream_sid: str | None
    started_at: datetime
    last_transcript: str
    active: bool
    processed_event_ids: set[str]


class SessionStateStore:
    """
    Lightweight in-memory session store for active Twilio conversation sessions.
    Intended for per-instance runtime state only.
    """

    def __init__(self):
        self._lock = Lock()
        self._sessions: dict[str, SessionState] = {}

    def start(self, conversation_id: str, consultation_id: str) -> None:
        with self._lock:
            self._sessions[conversation_id] = SessionState(
                conversation_id=conversation_id,
                consultation_id=consultation_id,
                stream_sid=None,
                started_at=datetime.now(timezone.utc),
                last_transcript="",
                active=True,
                processed_event_ids=set(),
            )

    def update_stream_sid(self, conversation_id: str, stream_sid: str) -> None:
        with self._lock:
            session = self._sessions.get(conversation_id)
            if session:
                session.stream_sid = stream_sid

    def update_transcript(self, conversation_id: str, transcript: str) -> None:
        with self._lock:
            session = self._sessions.get(conversation_id)
            if session:
                session.last_transcript = transcript

    def end(self, conversation_id: str) -> None:
        with self._lock:
            session = self._sessions.get(conversation_id)
            if session:
                session.active = False

    def mark_event_processed(self, conversation_id: str, event_id: str) -> bool:
        """
        Returns True if event is newly processed, False if duplicate/known.
        """
        with self._lock:
            session = self._sessions.get(conversation_id)
            if not session:
                return True
            if event_id in session.processed_event_ids:
                return False
            session.processed_event_ids.add(event_id)
            if len(session.processed_event_ids) > 5000:
                # Keep memory bounded for long sessions.
                session.processed_event_ids = set(list(session.processed_event_ids)[-3000:])
            return True

    def get(self, conversation_id: str) -> SessionState | None:
        with self._lock:
            return self._sessions.get(conversation_id)

    def cleanup(self, conversation_id: str) -> None:
        with self._lock:
            self._sessions.pop(conversation_id, None)


session_state_store = SessionStateStore()

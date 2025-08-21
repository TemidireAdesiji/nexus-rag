"""Thread-safe in-memory session store."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from typing import Any

from loguru import logger


class MemorySessionStore:
    """Manages conversation sessions in memory."""

    def __init__(
        self,
        max_messages: int = 200,
    ) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._max_messages = max_messages

    def open_session(self) -> dict[str, Any]:
        """Create a new session and return it."""
        sid = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        session: dict[str, Any] = {
            "session_id": sid,
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
        with self._lock:
            self._sessions[sid] = session
        logger.info("Session opened: {}", sid)
        return session

    def fetch_session(
        self,
        sid: str,
    ) -> dict[str, Any] | None:
        """Return session data or None."""
        with self._lock:
            return self._sessions.get(sid)

    def record_exchange(
        self,
        sid: str,
        question: str,
        answer: str,
        strategy: str = "vector",
    ) -> None:
        """Append a Q&A pair to the session."""
        now = datetime.now(UTC).isoformat()
        with self._lock:
            session = self._sessions.get(sid)
            if session is None:
                logger.warning(
                    "Cannot record to missing session {}",
                    sid,
                )
                return
            session["messages"].append(
                {
                    "role": "user",
                    "content": question,
                    "timestamp": now,
                    "strategy": strategy,
                },
            )
            session["messages"].append(
                {
                    "role": "assistant",
                    "content": answer,
                    "timestamp": now,
                    "strategy": strategy,
                },
            )
            if len(session["messages"]) > self._max_messages:
                excess = len(session["messages"]) - self._max_messages
                session["messages"] = session["messages"][excess:]
            session["updated_at"] = now

    def close_session(self, sid: str) -> bool:
        """Remove a session. Returns True if found."""
        with self._lock:
            if sid in self._sessions:
                del self._sessions[sid]
                logger.info(
                    "Session closed: {}",
                    sid,
                )
                return True
            return False

    def all_sessions(self) -> list[dict[str, Any]]:
        """Return summary list of all sessions."""
        with self._lock:
            return [
                {
                    "session_id": s["session_id"],
                    "created_at": s["created_at"],
                    "updated_at": s.get(
                        "updated_at",
                        s["created_at"],
                    ),
                    "message_count": len(
                        s["messages"],
                    ),
                }
                for s in self._sessions.values()
            ]

    def active_count(self) -> int:
        """Return number of active sessions."""
        with self._lock:
            return len(self._sessions)

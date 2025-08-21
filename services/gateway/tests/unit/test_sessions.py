"""Tests for the in-memory session store."""

from __future__ import annotations

from gateway.storage.sessions import (
    MemorySessionStore,
)


def test_open_session_returns_valid_structure(
    session_store: MemorySessionStore,
) -> None:
    """New session has expected fields."""
    session = session_store.open_session()
    assert "session_id" in session
    assert "created_at" in session
    assert isinstance(session["messages"], list)
    assert len(session["messages"]) == 0


def test_fetch_existing_session(
    session_store: MemorySessionStore,
) -> None:
    """Fetch returns the correct session."""
    session = session_store.open_session()
    sid = session["session_id"]
    fetched = session_store.fetch_session(sid)
    assert fetched is not None
    assert fetched["session_id"] == sid


def test_fetch_missing_session_returns_none(
    session_store: MemorySessionStore,
) -> None:
    """Fetch of nonexistent ID returns None."""
    result = session_store.fetch_session(
        "nonexistent",
    )
    assert result is None


def test_record_exchange_adds_messages(
    session_store: MemorySessionStore,
) -> None:
    """Recording an exchange adds two messages."""
    session = session_store.open_session()
    sid = session["session_id"]
    session_store.record_exchange(
        sid,
        "What is AI?",
        "AI is ...",
        "vector",
    )
    fetched = session_store.fetch_session(sid)
    assert fetched is not None
    assert len(fetched["messages"]) == 2
    assert fetched["messages"][0]["role"] == "user"
    assert fetched["messages"][1]["role"] == "assistant"


def test_record_exchange_trims_to_max(
    session_store: MemorySessionStore,
) -> None:
    """Messages beyond max are trimmed."""
    store = MemorySessionStore(max_messages=4)
    session = store.open_session()
    sid = session["session_id"]
    for i in range(5):
        store.record_exchange(
            sid,
            f"Q{i}",
            f"A{i}",
            "vector",
        )
    fetched = store.fetch_session(sid)
    assert fetched is not None
    assert len(fetched["messages"]) <= 4


def test_close_session_removes_it(
    session_store: MemorySessionStore,
) -> None:
    """Closing a session removes it."""
    session = session_store.open_session()
    sid = session["session_id"]
    assert session_store.close_session(sid) is True
    assert session_store.fetch_session(sid) is None


def test_close_nonexistent_returns_false(
    session_store: MemorySessionStore,
) -> None:
    """Closing a missing session returns False."""
    assert session_store.close_session("fake") is False


def test_all_sessions_returns_summaries(
    session_store: MemorySessionStore,
) -> None:
    """All sessions returns summary list."""
    session_store.open_session()
    session_store.open_session()
    summaries = session_store.all_sessions()
    assert len(summaries) == 2
    assert "session_id" in summaries[0]
    assert "message_count" in summaries[0]


def test_active_count_reflects_state(
    session_store: MemorySessionStore,
) -> None:
    """Active count matches open sessions."""
    assert session_store.active_count() == 0
    session_store.open_session()
    session_store.open_session()
    assert session_store.active_count() == 2


def test_record_on_missing_session_is_safe(
    session_store: MemorySessionStore,
) -> None:
    """Recording to a missing session is a no-op."""
    session_store.record_exchange(
        "missing",
        "Q",
        "A",
        "vector",
    )
    assert session_store.active_count() == 0

"""Session CRUD endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from loguru import logger

from gateway.middleware.auth import (
    verify_bearer_token,
)
from gateway.orchestrator import IntelligenceService

router = APIRouter(
    prefix="/api/conversations",
    tags=["sessions"],
    dependencies=[Depends(verify_bearer_token)],
)


def _get_service(
    request: Request,
) -> IntelligenceService:
    """Retrieve orchestrator from app state."""
    return request.app.state.service  # type: ignore[no-any-return]


ServiceDep = Annotated[
    IntelligenceService,
    Depends(_get_service),
]


@router.post("")
async def create_session(
    service: ServiceDep,
) -> dict[str, Any]:
    """Start a new conversation session."""
    session = service.sessions.open_session()
    logger.info(
        "Created session: {}",
        session["session_id"],
    )
    return session


@router.get("/{sid}")
async def get_session(
    sid: str,
    service: ServiceDep,
) -> dict[str, Any]:
    """Retrieve a session by ID."""
    session = service.sessions.fetch_session(sid)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )
    return session


@router.delete("/{sid}")
async def delete_session(
    sid: str,
    service: ServiceDep,
) -> dict[str, str]:
    """Remove a session."""
    removed = service.sessions.close_session(sid)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )
    return {"status": "deleted", "session_id": sid}


@router.get("")
async def list_sessions(
    service: ServiceDep,
) -> list[dict[str, Any]]:
    """List all active sessions."""
    return service.sessions.all_sessions()

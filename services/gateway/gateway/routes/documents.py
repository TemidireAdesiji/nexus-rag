"""Document upload and indexing endpoints."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
)
from loguru import logger

from gateway.middleware.auth import (
    verify_bearer_token,
)
from gateway.orchestrator import IntelligenceService

router = APIRouter(
    tags=["documents"],
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


@router.post("/api/ingest")
async def ingest_document(
    file: UploadFile,
    request: Request,
    service: ServiceDep,
) -> dict[str, Any]:
    """Upload and index a document."""
    settings = request.app.state.settings

    if file.filename is None:
        raise HTTPException(
            status_code=400,
            detail="No filename provided",
        )

    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(f"Unsupported file type: {suffix}"),
        )

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail="File exceeds size limit",
        )

    upload_path = os.path.join(
        settings.upload_dir,
        file.filename,
    )
    with open(upload_path, "wb") as f:
        f.write(content)

    result = service.ingest_document(upload_path)
    logger.info(
        "Ingested {}: {} chunks",
        file.filename,
        result["chunks_created"],
    )
    return result


@router.get("/api/search-modes")
async def list_search_modes(
    service: ServiceDep,
) -> list[dict[str, str]]:
    """List available retrieval strategies."""
    return service.available_strategies()

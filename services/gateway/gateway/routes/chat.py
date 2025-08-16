"""Chat endpoints for RAG queries."""

from __future__ import annotations

from typing import Annotated

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
from gateway.models import (
    CompletionRequest,
    CompletionResponse,
    InquiryRequest,
    InquiryResponse,
)
from gateway.orchestrator import IntelligenceService

router = APIRouter(tags=["chat"])


def _get_service(
    request: Request,
) -> IntelligenceService:
    """Retrieve the orchestrator from app state."""
    return request.app.state.service  # type: ignore[no-any-return]


ServiceDep = Annotated[
    IntelligenceService,
    Depends(_get_service),
]


@router.post(
    "/api/inquire",
    response_model=InquiryResponse,
    dependencies=[Depends(verify_bearer_token)],
)
async def inquire(
    body: InquiryRequest,
    service: ServiceDep,
) -> InquiryResponse:
    """Process a RAG question."""
    logger.info(
        "Inquiry: strategy={} session={}",
        body.strategy.value,
        body.session_id,
    )
    try:
        return service.answer_question(
            question=body.question,
            strategy=body.strategy,
            session_id=body.session_id,
            use_cache=body.use_cache,
        )
    except Exception as exc:
        logger.error("Inquiry failed: {}", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to process inquiry",
        ) from exc


@router.post(
    "/api/inquire/completions",
    response_model=CompletionResponse,
    dependencies=[Depends(verify_bearer_token)],
)
async def completions(
    body: CompletionRequest,
    service: ServiceDep,
) -> CompletionResponse:
    """OpenAI-compatible chat completion."""
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    try:
        return service.answer_openai_format(
            messages=messages,
            model=body.model,
            session_id=body.session_id,
            strategy=body.strategy,
        )
    except Exception as exc:
        logger.error("Completion failed: {}", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate completion",
        ) from exc

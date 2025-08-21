"""System health and information endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from gateway.orchestrator import IntelligenceService

router = APIRouter(tags=["system"])


def _get_service(
    request: Request,
) -> IntelligenceService:
    """Retrieve orchestrator from app state."""
    return request.app.state.service  # type: ignore[no-any-return]


ServiceDep = Annotated[
    IntelligenceService,
    Depends(_get_service),
]


@router.get("/alive")
async def liveness() -> dict[str, str]:
    """Liveness probe — always returns OK."""
    return {"status": "alive"}


@router.get("/ready")
async def readiness(
    service: ServiceDep,
) -> dict[str, Any]:
    """Readiness probe — checks pipeline state."""
    ready = service.pipeline_ready()
    return {
        "status": "ready" if ready else "warming",
        "pipeline_ready": ready,
    }


@router.get("/health")
async def health_check(
    service: ServiceDep,
) -> dict[str, Any]:
    """Detailed health information."""
    return service.platform_health()


@router.get("/api/platform/info")
async def platform_info(
    service: ServiceDep,
) -> dict[str, Any]:
    """System metadata and capabilities."""
    return service.platform_info()


@router.get("/api/platform/tools")
async def platform_tools(
    service: ServiceDep,
) -> dict[str, Any]:
    """Available agentic tools."""
    return {
        "tools": service.registry.descriptions(),
        "count": len(service.registry.catalog()),
    }

"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from gateway import __version__
from gateway.config import (
    GatewaySettings,
    load_settings,
)
from gateway.middleware.logging import setup_logging
from gateway.middleware.request_id import (
    RequestIdMiddleware,
)
from gateway.orchestrator import IntelligenceService
from gateway.routes import (
    chat,
    documents,
    sessions,
    system,
    websocket,
)


def build_app(
    settings: GatewaySettings | None = None,
) -> tuple[FastAPI, GatewaySettings]:
    """Construct the FastAPI application."""
    if settings is None:
        settings = load_settings()

    setup_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "NexusRAG — intelligent document retrieval and generation API"
        ),
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    app.include_router(system.router)
    app.include_router(chat.router)
    app.include_router(sessions.router)
    app.include_router(documents.router)
    app.include_router(websocket.router)

    service = IntelligenceService(settings)
    app.state.settings = settings
    app.state.service = service

    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info(
            "{} v{} starting on {}:{}",
            settings.app_name,
            __version__,
            settings.host,
            settings.port,
        )
        logger.info(
            "Environment: {}",
            settings.environment,
        )

    return app, settings


def run_server() -> None:
    """Launch the gateway with uvicorn."""
    import uvicorn

    app, settings = build_app()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )

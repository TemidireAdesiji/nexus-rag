"""Entry point for the NexusRAG gateway."""

from __future__ import annotations

import uvicorn

from gateway.config import load_settings
from gateway.main import build_app

settings = load_settings()
app, settings = build_app(settings)


def main() -> None:
    """Run the gateway server."""
    uvicorn.run(
        "gateway.server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()

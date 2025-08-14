"""Bearer-token authentication dependency."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request

from gateway.config import GatewaySettings


def _get_settings(
    request: Request,
) -> GatewaySettings:
    """Retrieve settings from app state."""
    return request.app.state.settings  # type: ignore[no-any-return]


async def verify_bearer_token(
    request: Request,
    settings: Annotated[
        GatewaySettings,
        Depends(_get_settings),
    ],
) -> None:
    """Validate the Authorization header token.

    Skipped when gateway_auth_enabled is False.
    """
    if not settings.gateway_auth_enabled:
        return

    auth_header: str | None = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization format",
        )

    if parts[1] != settings.gateway_bearer_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid bearer token",
        )

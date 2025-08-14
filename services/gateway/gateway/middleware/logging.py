"""Loguru configuration for structured logging."""

from __future__ import annotations

import sys

from loguru import logger

from gateway.config import GatewaySettings


def setup_logging(settings: GatewaySettings) -> None:
    """Configure loguru sinks based on settings."""
    logger.remove()

    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:"
        "<cyan>{function}</cyan>:"
        "<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=fmt,
        level=settings.log_level.upper(),
        colorize=True,
    )

    log_path = f"{settings.log_directory}/gateway.log"
    logger.add(
        log_path,
        format=fmt,
        level=settings.log_level.upper(),
        rotation=settings.log_rotation_size,
        retention=settings.log_retention_period,
        compression="zip",
        enqueue=True,
    )

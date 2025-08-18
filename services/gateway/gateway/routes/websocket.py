"""WebSocket chat endpoint."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket
from loguru import logger

from gateway.models import SearchStrategy
from gateway.orchestrator import IntelligenceService

router = APIRouter(tags=["websocket"])


async def _send_event(
    ws: WebSocket,
    event_type: str,
    data: dict[str, Any],
) -> None:
    """Send a typed event over WebSocket."""
    await ws.send_json(
        {"type": event_type, **data},
    )


@router.websocket("/ws/chat")
async def websocket_chat(
    ws: WebSocket,
) -> None:
    """Handle streaming chat over WebSocket."""
    await ws.accept()
    service: IntelligenceService = ws.app.state.service
    settings = ws.app.state.settings

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send_event(
                    ws,
                    "error",
                    {"message": "Invalid JSON"},
                )
                continue

            question = msg.get("question", "")
            if not question:
                await _send_event(
                    ws,
                    "error",
                    {"message": "Empty question"},
                )
                continue

            strategy_val = msg.get(
                "strategy",
                "vector",
            )
            try:
                strategy = SearchStrategy(
                    strategy_val,
                )
            except ValueError:
                strategy = SearchStrategy.VECTOR

            session_id = msg.get("session_id")

            await _send_event(
                ws,
                "thinking",
                {"message": "Processing query..."},
            )

            try:
                result = service.answer_question(
                    question=question,
                    strategy=strategy,
                    session_id=session_id,
                )

                await _send_event(
                    ws,
                    "status",
                    {
                        "message": ("Generating response"),
                    },
                )

                answer = result.answer
                chunk_size = settings.ws_chunk_bytes
                pause = settings.ws_chunk_pause_seconds

                for i in range(
                    0,
                    len(answer),
                    chunk_size,
                ):
                    chunk = answer[i : i + chunk_size]
                    await _send_event(
                        ws,
                        "chunk",
                        {"content": chunk},
                    )
                    await asyncio.sleep(pause)

                await _send_event(
                    ws,
                    "complete",
                    {
                        "question": question,
                        "strategy": (strategy.value),
                        "session_id": session_id,
                        "sources": result.sources,
                        "elapsed_seconds": (result.elapsed_seconds),
                    },
                )

            except Exception as exc:
                logger.error(
                    "WebSocket query failed: {}",
                    exc,
                )
                await _send_event(
                    ws,
                    "error",
                    {"message": str(exc)},
                )

    except Exception:
        logger.info("WebSocket connection closed")

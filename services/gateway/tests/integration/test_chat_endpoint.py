"""Integration tests for chat endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gateway.config import GatewaySettings
from gateway.models import InquiryResponse


def _build_test_app() -> FastAPI:
    """Build a test app with mocked services."""
    settings = GatewaySettings(
        environment="testing",
        gateway_auth_enabled=False,
        log_directory="/tmp/nexus_int_logs",
        upload_dir="/tmp/nexus_int_uploads",
        vector_store_path="/tmp/nexus_int_vec",
    )
    settings.ensure_dirs()

    app = FastAPI()

    from gateway.routes import chat, system

    app.include_router(chat.router)
    app.include_router(system.router)

    service = MagicMock()
    service.answer_question.return_value = InquiryResponse(
        answer="Test answer",
        question="Test?",
        strategy="vector",
        session_id=None,
        sources=[],
        tool_trace=[],
        elapsed_seconds=0.1,
        cached=False,
    )
    service.pipeline_ready.return_value = True
    service.platform_health.return_value = {
        "status": "healthy",
    }
    service.platform_info.return_value = {
        "name": "test",
        "version": "1.0.0",
    }
    service.registry = MagicMock()
    service.registry.catalog.return_value = []
    service.registry.descriptions.return_value = []

    app.state.service = service
    app.state.settings = settings
    return app


@pytest.fixture()
def client() -> TestClient:
    """TestClient for integration tests."""
    return TestClient(_build_test_app())


def test_inquire_returns_200(
    client: TestClient,
) -> None:
    """POST /api/inquire returns success."""
    resp = client.post(
        "/api/inquire",
        json={
            "question": "What is NexusRAG?",
            "strategy": "vector",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data


def test_inquire_with_session(
    client: TestClient,
) -> None:
    """Inquire with session_id works."""
    resp = client.post(
        "/api/inquire",
        json={
            "question": "Tell me more",
            "session_id": "abc-123",
        },
    )
    assert resp.status_code == 200


def test_inquire_empty_question(
    client: TestClient,
) -> None:
    """Empty question is rejected."""
    resp = client.post(
        "/api/inquire",
        json={"question": ""},
    )
    assert resp.status_code == 422


def test_inquire_invalid_strategy(
    client: TestClient,
) -> None:
    """Invalid strategy is rejected."""
    resp = client.post(
        "/api/inquire",
        json={
            "question": "Test",
            "strategy": "invalid",
        },
    )
    assert resp.status_code == 422


def test_alive_endpoint(
    client: TestClient,
) -> None:
    """Liveness probe returns alive."""
    resp = client.get("/alive")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_ready_endpoint(
    client: TestClient,
) -> None:
    """Readiness probe returns status."""
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert "pipeline_ready" in resp.json()


def test_health_endpoint(
    client: TestClient,
) -> None:
    """Health endpoint returns details."""
    resp = client.get("/health")
    assert resp.status_code == 200


def test_platform_info(
    client: TestClient,
) -> None:
    """Platform info returns metadata."""
    resp = client.get("/api/platform/info")
    assert resp.status_code == 200
    assert "name" in resp.json()


def test_platform_tools(
    client: TestClient,
) -> None:
    """Platform tools returns tool list."""
    resp = client.get("/api/platform/tools")
    assert resp.status_code == 200
    assert "tools" in resp.json()

"""Integration tests for document upload."""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gateway.config import GatewaySettings


def _build_test_app() -> FastAPI:
    """Build a test app with mocked services."""
    settings = GatewaySettings(
        environment="testing",
        gateway_auth_enabled=False,
        log_directory="/tmp/nexus_doc_logs",
        upload_dir="/tmp/nexus_doc_uploads",
        vector_store_path="/tmp/nexus_doc_vec",
        allowed_extensions=[
            ".txt",
            ".md",
            ".pdf",
        ],
    )
    settings.ensure_dirs()

    app = FastAPI()

    from gateway.routes import documents

    app.include_router(documents.router)

    service = MagicMock()
    service.ingest_document.return_value = {
        "file": "test.txt",
        "chunks_created": 3,
        "status": "indexed",
    }
    service.available_strategies.return_value = [
        {"value": "vector", "label": "Vector"},
    ]

    app.state.service = service
    app.state.settings = settings
    return app


@pytest.fixture()
def client() -> TestClient:
    """TestClient for upload tests."""
    return TestClient(_build_test_app())


def test_ingest_valid_file(
    client: TestClient,
) -> None:
    """Uploading a valid file succeeds."""
    content = b"Test document content here."
    resp = client.post(
        "/api/ingest",
        files={
            "file": (
                "test.txt",
                io.BytesIO(content),
                "text/plain",
            ),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "indexed"


def test_ingest_unsupported_extension(
    client: TestClient,
) -> None:
    """Unsupported file type is rejected."""
    resp = client.post(
        "/api/ingest",
        files={
            "file": (
                "script.exe",
                io.BytesIO(b"data"),
                "application/octet-stream",
            ),
        },
    )
    assert resp.status_code == 400


def test_ingest_markdown_file(
    client: TestClient,
) -> None:
    """Markdown files are accepted."""
    content = b"# Heading\nSome content."
    resp = client.post(
        "/api/ingest",
        files={
            "file": (
                "readme.md",
                io.BytesIO(content),
                "text/markdown",
            ),
        },
    )
    assert resp.status_code == 200


def test_search_modes_endpoint(
    client: TestClient,
) -> None:
    """Search modes returns strategy list."""
    resp = client.get("/api/search-modes")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_ingest_oversized_file(
    client: TestClient,
) -> None:
    """Oversized file is rejected with 413."""
    app = client.app
    app.state.settings.max_content_length_mb = 0

    content = b"x" * 1024
    resp = client.post(
        "/api/ingest",
        files={
            "file": (
                "big.txt",
                io.BytesIO(content),
                "text/plain",
            ),
        },
    )
    assert resp.status_code == 413


def test_ingest_pdf_extension(
    client: TestClient,
) -> None:
    """PDF extension is accepted."""
    resp = client.post(
        "/api/ingest",
        files={
            "file": (
                "report.pdf",
                io.BytesIO(b"%PDF-1.4 fake"),
                "application/pdf",
            ),
        },
    )
    assert resp.status_code == 200

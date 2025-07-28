"""Shared fixtures for the test suite."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from gateway.config import GatewaySettings
from gateway.storage.cache import QueryResultCache
from gateway.storage.rate_limiter import (
    SlidingWindowLimiter,
)
from gateway.storage.sessions import (
    MemorySessionStore,
)


@pytest.fixture()
def settings() -> GatewaySettings:
    """Test-oriented gateway settings."""
    return GatewaySettings(
        environment="testing",
        debug=True,
        host="127.0.0.1",
        port=9999,
        gateway_auth_enabled=False,
        data_api_url="http://test-api:5000",
        log_directory="/tmp/nexus_test_logs",
        upload_dir="/tmp/nexus_test_uploads",
        vector_store_path="/tmp/nexus_test_vec",
        cache_capacity=16,
        max_messages_per_session=10,
        requests_per_minute=5,
        reranking_enabled=False,
    )


@pytest.fixture()
def mock_data_client() -> MagicMock:
    """Mock DataServiceClient."""
    client = MagicMock()
    client.is_reachable.return_value = True
    client.ping.return_value = {
        "status": "healthy",
    }
    client.query_team.return_value = {
        "name": "Alice Smith",
        "role": "Engineer",
    }
    client.query_portfolio.return_value = {
        "company": "Acme Corp",
        "status": "active",
    }
    client.query_verticals.return_value = {
        "sector": "technology",
        "companies": 5,
    }
    client.query_engagements.return_value = {
        "engagements": [],
    }
    client.query_web_content.return_value = {
        "content": "Sample web content",
    }
    client.registered_tool_names.return_value = [
        "query_team",
        "query_portfolio",
    ]
    client.download_corpus_archive.side_effect = ConnectionError("Test mode")
    return client


@pytest.fixture()
def session_store() -> MemorySessionStore:
    """Fresh session store for testing."""
    return MemorySessionStore(max_messages=10)


@pytest.fixture()
def cache() -> QueryResultCache:
    """Small test cache."""
    return QueryResultCache(capacity=4)


@pytest.fixture()
def rate_limiter() -> SlidingWindowLimiter:
    """Strict test rate limiter."""
    return SlidingWindowLimiter(
        requests_per_minute=3,
    )


@pytest.fixture()
def sample_documents() -> list[Document]:
    """Collection of test documents."""
    return [
        Document(
            page_content=(
                "The venture capital fund raised "
                "two billion dollars in its latest "
                "fundraising round."
            ),
            metadata={
                "source": "report_a.txt",
                "origin": "test",
            },
        ),
        Document(
            page_content=(
                "Machine learning models are "
                "transforming how businesses "
                "analyse customer data."
            ),
            metadata={
                "source": "report_b.txt",
                "origin": "test",
            },
        ),
        Document(
            page_content=(
                "The healthcare sector continues "
                "to see strong growth driven by "
                "digital innovation."
            ),
            metadata={
                "source": "report_c.txt",
                "origin": "test",
            },
        ),
        Document(
            page_content=(
                "Renewable energy investments "
                "exceeded expectations in the "
                "fourth quarter results."
            ),
            metadata={
                "source": "report_d.txt",
                "origin": "test",
            },
        ),
        Document(
            page_content=(
                "Software engineering best "
                "practices include continuous "
                "integration and code review."
            ),
            metadata={
                "source": "report_e.txt",
                "origin": "test",
            },
        ),
    ]

"""Application configuration via Pydantic settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import (
    Field,
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class GatewaySettings(BaseSettings):
    """Centralised config for the NexusRAG gateway."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- app metadata ---------------------------------
    app_name: str = "NexusRAG Gateway"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = Field(
        default="change-me-in-production",
    )

    # -- CORS -----------------------------------------
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
    )

    # -- uploads --------------------------------------
    max_content_length_mb: int = 50
    upload_dir: str = "uploads"
    allowed_extensions: list[str] = Field(
        default_factory=lambda: [
            ".txt",
            ".md",
            ".pdf",
            ".docx",
        ],
    )

    # -- backend data API -----------------------------
    data_api_url: str = "http://localhost:5000"
    data_api_token: str = ""
    data_api_timeout_seconds: int = 30

    # -- gateway auth ---------------------------------
    gateway_auth_enabled: bool = False
    gateway_bearer_token: str = ""

    # -- ML models ------------------------------------
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model_name: str = "llama3"
    reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # -- chunking -------------------------------------
    chunk_length: int = 1000
    chunk_overlap_length: int = 200

    # -- retrieval ------------------------------------
    result_limit: int = 5
    relevance_threshold: float = 0.25
    reranking_enabled: bool = True
    hybrid_search_enabled: bool = True

    # -- vector store ---------------------------------
    vector_store_path: str = "vector_data"
    vector_collection: str = "nexus_docs"

    # -- memory ---------------------------------------
    conversation_memory_key: str = "chat_history"
    conversation_window_size: int = 8

    # -- session --------------------------------------
    max_messages_per_session: int = 200
    max_query_length: int = 2000
    cache_capacity: int = 256

    # -- logging --------------------------------------
    log_directory: str = "logs"
    log_level: str = "INFO"
    log_rotation_size: str = "10 MB"
    log_retention_period: str = "7 days"

    # -- websocket ------------------------------------
    ws_chunk_bytes: int = 512
    ws_chunk_pause_seconds: float = 0.05

    # -- rate limiting --------------------------------
    rate_limiting_enabled: bool = False
    requests_per_minute: int = 60

    # -- validators -----------------------------------
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(
        cls,
        value: Any,
    ) -> list[str]:
        """Accept comma-separated string or list."""
        if isinstance(value, str):
            return [
                origin.strip() for origin in value.split(",") if origin.strip()
            ]
        return list(value)

    @model_validator(mode="after")
    def validate_auth_config(
        self,
    ) -> GatewaySettings:
        """Ensure token is set when auth is on."""
        if self.gateway_auth_enabled and not self.gateway_bearer_token:
            raise ValueError(
                "gateway_bearer_token is required"
                " when gateway_auth_enabled is True"
            )
        return self

    # -- helpers --------------------------------------
    @property
    def max_upload_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.max_content_length_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        """Create required directories."""
        for directory in (
            self.upload_dir,
            self.vector_store_path,
            self.log_directory,
        ):
            os.makedirs(directory, exist_ok=True)


def load_settings() -> GatewaySettings:
    """Build and return validated settings."""
    settings = GatewaySettings()
    settings.ensure_dirs()
    return settings


_root = Path(__file__).resolve().parent.parent
_env_path = _root / ".env"

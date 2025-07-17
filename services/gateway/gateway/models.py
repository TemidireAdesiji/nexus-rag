"""Shared Pydantic models and data structures."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class SearchStrategy(enum.StrEnum):
    """Available retrieval strategies."""

    VECTOR = "vector"
    COMBINED = "combined"
    EXPANDED = "expanded"
    DECOMPOSED = "decomposed"


STRATEGY_LABELS: dict[SearchStrategy, str] = {
    SearchStrategy.VECTOR: "Vector similarity search",
    SearchStrategy.COMBINED: ("Hybrid vector + keyword search"),
    SearchStrategy.EXPANDED: ("Multi-query expansion search"),
    SearchStrategy.DECOMPOSED: ("Query decomposition search"),
}


@dataclass
class SearchOutcome:
    """Result container for a retrieval operation."""

    documents: list[Any] = field(
        default_factory=list,
    )
    scores: list[float] = field(
        default_factory=list,
    )
    query: str = ""
    strategy: SearchStrategy = SearchStrategy.VECTOR
    elapsed_seconds: float = 0.0
    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


# -- request / response models ----------------------


class InquiryRequest(BaseModel):
    """Incoming question payload."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user question",
    )
    strategy: SearchStrategy = Field(
        default=SearchStrategy.VECTOR,
        description="Retrieval strategy",
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session identifier",
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to use result cache",
    )


class InquiryResponse(BaseModel):
    """Outgoing answer payload."""

    answer: str
    question: str
    strategy: str
    session_id: str | None = None
    sources: list[dict[str, Any]] = Field(
        default_factory=list,
    )
    tool_trace: list[dict[str, Any]] = Field(
        default_factory=list,
    )
    elapsed_seconds: float = 0.0
    cached: bool = False


class CompletionMessage(BaseModel):
    """Single message in OpenAI format."""

    role: str = "user"
    content: str = ""


class CompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    messages: list[CompletionMessage] = Field(
        ...,
        min_length=1,
    )
    model: str = "nexus-rag"
    session_id: str | None = None
    strategy: SearchStrategy = Field(
        default=SearchStrategy.VECTOR,
    )
    stream: bool = False


class CompletionChoice(BaseModel):
    """Single completion choice."""

    index: int = 0
    message: CompletionMessage = Field(
        default_factory=lambda: CompletionMessage(
            role="assistant",
            content="",
        ),
    )
    finish_reason: str = "stop"


class CompletionUsage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class CompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str = ""
    object: str = "chat.completion"
    created: int = Field(
        default_factory=lambda: int(time.time()),
    )
    model: str = "nexus-rag"
    choices: list[CompletionChoice] = Field(
        default_factory=list,
    )
    usage: CompletionUsage = Field(
        default_factory=CompletionUsage,
    )

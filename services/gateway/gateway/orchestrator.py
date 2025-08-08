"""Central coordinator for all RAG operations."""

from __future__ import annotations

import hashlib
import json
import platform
import time
from typing import Any

from loguru import logger

from gateway import __version__
from gateway.agents.executor import (
    ActionExecutor,
)
from gateway.agents.planner import ActionPlanner
from gateway.agents.tools import ToolRegistry
from gateway.clients.data_api import (
    DataServiceClient,
)
from gateway.config import GatewaySettings
from gateway.entities import (
    extract_named_entities,
)
from gateway.generation.llm import LanguageModel
from gateway.generation.response import (
    AnswerComposer,
)
from gateway.models import (
    STRATEGY_LABELS,
    CompletionChoice,
    CompletionMessage,
    CompletionResponse,
    InquiryResponse,
    SearchStrategy,
)
from gateway.retrieval.engine import (
    RetrievalPipeline,
)
from gateway.storage.cache import QueryResultCache
from gateway.storage.sessions import (
    MemorySessionStore,
)


class IntelligenceService:
    """Orchestrate retrieval, generation, agents."""

    def __init__(
        self,
        settings: GatewaySettings,
    ) -> None:
        self._settings = settings

        self._data_client = DataServiceClient(
            base_url=settings.data_api_url,
            token=settings.data_api_token,
            timeout_seconds=(settings.data_api_timeout_seconds),
        )

        self._llm = LanguageModel(
            model_name=settings.llm_model_name,
        )

        self._pipeline = RetrievalPipeline(
            config=settings,
            data_client=self._data_client,
            llm=self._llm.underlying,
        )

        self._composer = AnswerComposer(
            llm=self._llm.underlying,
            memory_window=(settings.conversation_window_size),
        )

        self._registry = ToolRegistry.build_from_client(
            self._data_client,
        )
        self._planner = ActionPlanner(
            llm=self._llm.underlying,
        )
        self._executor = ActionExecutor()

        self._sessions = MemorySessionStore(
            max_messages=(settings.max_messages_per_session),
        )
        self._cache = QueryResultCache(
            capacity=settings.cache_capacity,
        )

        logger.info("IntelligenceService initialised")

    def answer_question(
        self,
        question: str,
        strategy: SearchStrategy = (SearchStrategy.VECTOR),
        session_id: str | None = None,
        use_cache: bool = True,
    ) -> InquiryResponse:
        """Full RAG pipeline execution."""
        start = time.perf_counter()
        cache_key = self._make_cache_key(
            question,
            strategy,
        )

        if use_cache:
            cached = self._cache.lookup(cache_key)
            if cached is not None:
                logger.info(
                    "Cache hit for: {}",
                    question[:50],
                )
                cached["cached"] = True
                return InquiryResponse(**cached)

        outcome = self._pipeline.search(
            question,
            strategy,
        )

        entities = extract_named_entities(question)

        plan = self._planner.devise_plan(
            query=question,
            entities=entities,
            context="",
            registry=self._registry,
        )
        api_data, exec_log = self._executor.run_plan(
            plan,
            self._registry,
            self._data_client,
        )

        api_context = (
            json.dumps(
                api_data,
                default=str,
            )
            if api_data
            else ""
        )
        tool_trace = ActionExecutor.format_trace(exec_log)

        history: list[dict[str, Any]] = []
        if session_id:
            session = self._sessions.fetch_session(
                session_id,
            )
            if session:
                history = session.get(
                    "messages",
                    [],
                )

        answer = self._composer.compose(
            query=question,
            retrieved=outcome.documents,
            api_context=api_context,
            api_trace=tool_trace,
            history=history,
        )

        elapsed = time.perf_counter() - start

        sources = [
            {
                "content": (doc.page_content[:200]),
                "metadata": doc.metadata,
            }
            for doc in outcome.documents
        ]

        response = InquiryResponse(
            answer=answer,
            question=question,
            strategy=strategy.value,
            session_id=session_id,
            sources=sources,
            tool_trace=tool_trace,
            elapsed_seconds=round(elapsed, 4),
            cached=False,
        )

        if session_id:
            self._sessions.record_exchange(
                session_id,
                question,
                answer,
                strategy.value,
            )

        if use_cache:
            self._cache.store(
                cache_key,
                response.model_dump(),
            )

        return response

    def answer_openai_format(
        self,
        messages: list[dict[str, str]],
        model: str = "nexus-rag",
        session_id: str | None = None,
        strategy: SearchStrategy = (SearchStrategy.VECTOR),
    ) -> CompletionResponse:
        """OpenAI-compatible chat completion."""
        user_msgs = [m for m in messages if m.get("role") == "user"]
        question = user_msgs[-1]["content"] if user_msgs else ""

        if not question:
            return CompletionResponse(
                id="nexus-empty",
                model=model,
                choices=[
                    CompletionChoice(
                        message=CompletionMessage(
                            role="assistant",
                            content=("No question provided."),
                        ),
                    ),
                ],
            )

        result = self.answer_question(
            question=question,
            strategy=strategy,
            session_id=session_id,
        )

        return CompletionResponse(
            id=f"nexus-{int(time.time())}",
            model=model,
            choices=[
                CompletionChoice(
                    message=CompletionMessage(
                        role="assistant",
                        content=result.answer,
                    ),
                ),
            ],
        )

    def ingest_document(
        self,
        filepath: str,
    ) -> dict[str, Any]:
        """Index an uploaded document."""
        chunk_count = self._pipeline.indexer.ingest_file(
            filepath,
        )
        return {
            "file": filepath,
            "chunks_created": chunk_count,
            "status": ("indexed" if chunk_count > 0 else "empty"),
        }

    def available_strategies(
        self,
    ) -> list[dict[str, str]]:
        """List all retrieval strategies."""
        return [
            {
                "value": s.value,
                "label": STRATEGY_LABELS[s],
            }
            for s in SearchStrategy
        ]

    def platform_health(
        self,
    ) -> dict[str, Any]:
        """Detailed health check."""
        backend_ok = self._data_client.is_reachable()
        return {
            "status": ("healthy" if backend_ok else "degraded"),
            "backend_reachable": backend_ok,
            "pipeline_ready": (self._pipeline.is_warmed_up),
            "sessions_active": (self._sessions.active_count()),
            "cache_size": (self._cache.current_size()),
        }

    def platform_info(
        self,
    ) -> dict[str, Any]:
        """System metadata."""
        return {
            "name": self._settings.app_name,
            "version": __version__,
            "environment": (self._settings.environment),
            "python_version": platform.python_version(),
            "llm_model": self._llm.model_id,
            "embedding_model": (self._settings.embedding_model_name),
            "strategies": [s.value for s in SearchStrategy],
            "tools": self._registry.catalog(),
        }

    def pipeline_ready(self) -> bool:
        """Whether the retrieval pipeline is warm."""
        return self._pipeline.is_warmed_up

    def warm_up_pipeline(self) -> None:
        """Load documents and build indexes."""
        self._pipeline.warm_up()

    @property
    def sessions(self) -> MemorySessionStore:
        """Access the session store."""
        return self._sessions

    @property
    def registry(self) -> ToolRegistry:
        """Access the tool registry."""
        return self._registry

    @staticmethod
    def _make_cache_key(
        question: str,
        strategy: SearchStrategy,
    ) -> str:
        """Deterministic cache key."""
        raw = f"{question}|{strategy.value}"
        return hashlib.sha256(
            raw.encode(),
        ).hexdigest()

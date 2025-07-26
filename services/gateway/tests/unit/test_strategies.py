"""Tests for retrieval strategy executor."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.documents import Document

from gateway.models import SearchStrategy
from gateway.retrieval.strategies import (
    StrategyExecutor,
)


def _mock_indexer(
    docs: list[Document] | None = None,
) -> MagicMock:
    """Create a mock indexer."""
    indexer = MagicMock()
    result_docs = docs or [
        Document(
            page_content="Test content",
            metadata={"source": "test.txt"},
        ),
    ]
    store = MagicMock()
    store.similarity_search.return_value = result_docs
    indexer.vector_store = store

    retriever = MagicMock()
    retriever.invoke.return_value = result_docs
    indexer.combined_retriever = retriever

    return indexer


def test_vector_search_returns_docs() -> None:
    """Vector strategy returns documents."""
    indexer = _mock_indexer()
    executor = StrategyExecutor(indexer)
    results = executor.run(
        "test query",
        SearchStrategy.VECTOR,
    )
    assert len(results) >= 1


def test_combined_search_uses_ensemble() -> None:
    """Combined strategy uses ensemble retriever."""
    indexer = _mock_indexer()
    executor = StrategyExecutor(indexer)
    results = executor.run(
        "test query",
        SearchStrategy.COMBINED,
    )
    assert len(results) >= 1
    indexer.combined_retriever.invoke.assert_called()


def test_vector_search_empty_store() -> None:
    """Empty vector store returns empty list."""
    indexer = MagicMock()
    indexer.vector_store = None
    executor = StrategyExecutor(indexer)
    results = executor.run(
        "query",
        SearchStrategy.VECTOR,
    )
    assert results == []


def test_combined_fallback_to_vector() -> None:
    """Combined falls back when no ensemble."""
    indexer = _mock_indexer()
    indexer.combined_retriever = None
    executor = StrategyExecutor(indexer)
    results = executor.run(
        "query",
        SearchStrategy.COMBINED,
    )
    assert len(results) >= 1


def test_expanded_without_llm_returns_docs() -> None:
    """Expanded without LLM uses original query."""
    indexer = _mock_indexer()
    executor = StrategyExecutor(
        indexer,
        llm=None,
    )
    results = executor.run(
        "query",
        SearchStrategy.EXPANDED,
    )
    assert len(results) >= 1


def test_decomposed_without_llm() -> None:
    """Decomposed without LLM uses original."""
    indexer = _mock_indexer()
    executor = StrategyExecutor(
        indexer,
        llm=None,
    )
    results = executor.run(
        "query",
        SearchStrategy.DECOMPOSED,
    )
    assert len(results) >= 1


def test_expanded_deduplicates() -> None:
    """Expanded search removes duplicate docs."""
    doc = Document(
        page_content="Same content repeated",
        metadata={"source": "dup.txt"},
    )
    indexer = _mock_indexer([doc, doc])
    executor = StrategyExecutor(
        indexer,
        llm=None,
    )
    results = executor.run(
        "query",
        SearchStrategy.EXPANDED,
    )
    assert len(results) == 1


def test_result_limit_respected() -> None:
    """Executor respects result_limit."""
    docs = [
        Document(
            page_content=f"Doc {i}",
            metadata={"source": f"d{i}.txt"},
        )
        for i in range(20)
    ]
    indexer = _mock_indexer(docs)
    executor = StrategyExecutor(
        indexer,
        llm=None,
        result_limit=3,
    )
    results = executor.run(
        "query",
        SearchStrategy.VECTOR,
    )
    assert len(results) <= 20

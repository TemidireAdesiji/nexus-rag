"""Tests for the document indexer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from gateway.config import GatewaySettings
from gateway.retrieval.indexer import (
    DocumentIndexer,
)


def _test_settings() -> GatewaySettings:
    """Minimal settings for indexer tests."""
    return GatewaySettings(
        chunk_length=100,
        chunk_overlap_length=20,
        result_limit=3,
        vector_store_path="/tmp/test_vec",
        vector_collection="test_col",
        embedding_model_name=("sentence-transformers/all-MiniLM-L6-v2"),
    )


def _sample_docs() -> list[Document]:
    """Create sample documents."""
    return [
        Document(
            page_content="A" * 250,
            metadata={"source": "a.txt"},
        ),
        Document(
            page_content="B" * 300,
            metadata={"source": "b.txt"},
        ),
    ]


@patch(
    "gateway.retrieval.indexer.HuggingFaceEmbeddings",
)
def test_segment_documents_splits(
    mock_emb: MagicMock,
) -> None:
    """Segmenting produces more chunks than docs."""
    indexer = DocumentIndexer(_test_settings())
    docs = _sample_docs()
    chunks = indexer.segment_documents(docs)
    assert len(chunks) > len(docs)


@patch(
    "gateway.retrieval.indexer.HuggingFaceEmbeddings",
)
def test_segment_preserves_metadata(
    mock_emb: MagicMock,
) -> None:
    """Chunks retain source metadata."""
    indexer = DocumentIndexer(_test_settings())
    docs = _sample_docs()
    chunks = indexer.segment_documents(docs)
    for chunk in chunks:
        assert "source" in chunk.metadata


@patch(
    "gateway.retrieval.indexer.HuggingFaceEmbeddings",
)
def test_chunk_count_starts_at_zero(
    mock_emb: MagicMock,
) -> None:
    """Chunk count is zero before indexing."""
    indexer = DocumentIndexer(_test_settings())
    assert indexer.chunk_count == 0


@patch(
    "gateway.retrieval.indexer.HuggingFaceEmbeddings",
)
def test_vector_store_initially_none(
    mock_emb: MagicMock,
) -> None:
    """Vector store is None before building."""
    indexer = DocumentIndexer(_test_settings())
    assert indexer.vector_store is None


@patch(
    "gateway.retrieval.indexer.HuggingFaceEmbeddings",
)
def test_keyword_retriever_initially_none(
    mock_emb: MagicMock,
) -> None:
    """BM25 retriever is None before building."""
    indexer = DocumentIndexer(_test_settings())
    assert indexer.keyword_retriever is None


@patch(
    "gateway.retrieval.indexer.HuggingFaceEmbeddings",
)
def test_combined_retriever_initially_none(
    mock_emb: MagicMock,
) -> None:
    """Ensemble retriever is None initially."""
    indexer = DocumentIndexer(_test_settings())
    assert indexer.combined_retriever is None


@patch(
    "gateway.retrieval.indexer.HuggingFaceEmbeddings",
)
def test_segment_empty_list(
    mock_emb: MagicMock,
) -> None:
    """Segmenting empty list returns empty."""
    indexer = DocumentIndexer(_test_settings())
    chunks = indexer.segment_documents([])
    assert chunks == []


@patch(
    "gateway.retrieval.indexer.HuggingFaceEmbeddings",
)
def test_build_combined_without_stores(
    mock_emb: MagicMock,
) -> None:
    """Combined index returns None with no stores."""
    indexer = DocumentIndexer(_test_settings())
    result = indexer.build_combined_index()
    assert result is None

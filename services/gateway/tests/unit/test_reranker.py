"""Tests for the cross-encoder reranker."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
from langchain_core.documents import Document

from gateway.retrieval.reranker import (
    CrossEncoderReranker,
)


def _make_docs(count: int) -> list[Document]:
    """Generate test documents."""
    return [
        Document(
            page_content=f"Document number {i}",
            metadata={"source": f"doc_{i}.txt"},
        )
        for i in range(count)
    ]


@patch(
    "sentence_transformers.CrossEncoder",
)
def test_reorder_sorts_by_score(
    mock_ce_cls: MagicMock,
) -> None:
    """Documents are sorted descending by score."""
    encoder = MagicMock()
    encoder.predict.return_value = np.array(
        [0.1, 0.9, 0.5],
    )
    mock_ce_cls.return_value = encoder

    reranker = CrossEncoderReranker()
    docs = _make_docs(3)
    ranked, scores = reranker.reorder(
        "query",
        docs,
    )
    assert scores[0] > scores[-1]
    assert ranked[0].page_content == ("Document number 1")


@patch(
    "sentence_transformers.CrossEncoder",
)
def test_reorder_empty_returns_empty(
    mock_ce_cls: MagicMock,
) -> None:
    """Empty input returns empty output."""
    reranker = CrossEncoderReranker()
    ranked, scores = reranker.reorder("q", [])
    assert ranked == []
    assert scores == []


@patch(
    "sentence_transformers.CrossEncoder",
)
def test_reorder_single_document(
    mock_ce_cls: MagicMock,
) -> None:
    """Single document is returned as-is."""
    encoder = MagicMock()
    encoder.predict.return_value = np.array([0.8])
    mock_ce_cls.return_value = encoder

    reranker = CrossEncoderReranker()
    docs = _make_docs(1)
    ranked, scores = reranker.reorder("q", docs)
    assert len(ranked) == 1
    assert scores == [0.8]


@patch(
    "sentence_transformers.CrossEncoder",
)
def test_reorder_preserves_metadata(
    mock_ce_cls: MagicMock,
) -> None:
    """Metadata is kept after reranking."""
    encoder = MagicMock()
    encoder.predict.return_value = np.array(
        [0.3, 0.7],
    )
    mock_ce_cls.return_value = encoder

    reranker = CrossEncoderReranker()
    docs = _make_docs(2)
    ranked, _ = reranker.reorder("q", docs)
    assert "source" in ranked[0].metadata


@patch(
    "sentence_transformers.CrossEncoder",
)
def test_scores_are_floats(
    mock_ce_cls: MagicMock,
) -> None:
    """Scores are Python floats."""
    encoder = MagicMock()
    encoder.predict.return_value = np.array(
        [0.5, 0.2],
    )
    mock_ce_cls.return_value = encoder

    reranker = CrossEncoderReranker()
    docs = _make_docs(2)
    _, scores = reranker.reorder("q", docs)
    assert all(isinstance(s, float) for s in scores)


@patch(
    "sentence_transformers.CrossEncoder",
)
def test_lazy_model_loading(
    mock_ce_cls: MagicMock,
) -> None:
    """Model loads only on first use."""
    reranker = CrossEncoderReranker()
    mock_ce_cls.assert_not_called()
    encoder = MagicMock()
    encoder.predict.return_value = np.array([0.5])
    mock_ce_cls.return_value = encoder
    reranker.reorder("q", _make_docs(1))
    mock_ce_cls.assert_called_once()

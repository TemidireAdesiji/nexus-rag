"""Cross-encoder reranking for retrieved documents."""

from __future__ import annotations

from langchain_core.documents import Document
from loguru import logger


class CrossEncoderReranker:
    """Rerank documents using a cross-encoder model."""

    def __init__(
        self,
        model_name: str = ("cross-encoder/ms-marco-MiniLM-L-6-v2"),
    ) -> None:
        self._model_name = model_name
        self._encoder: object | None = None

    def _load_model(self) -> None:
        """Lazy-load the cross-encoder model."""
        if self._encoder is not None:
            return
        from sentence_transformers import (
            CrossEncoder,
        )

        self._encoder = CrossEncoder(
            self._model_name,
        )
        logger.info(
            "Loaded reranker model: {}",
            self._model_name,
        )

    def reorder(
        self,
        query: str,
        documents: list[Document],
    ) -> tuple[list[Document], list[float]]:
        """Score and reorder documents by relevance.

        Returns sorted documents and their scores.
        """
        if not documents:
            return [], []

        self._load_model()

        pairs = [[query, doc.page_content] for doc in documents]
        raw_scores = self._encoder.predict(  # type: ignore[union-attr]
            pairs,
        )
        scores = [float(s) for s in raw_scores]

        scored = list(
            zip(documents, scores, strict=True),
        )
        scored.sort(key=lambda x: x[1], reverse=True)

        ranked_docs = [item[0] for item in scored]
        ranked_scores = [item[1] for item in scored]

        logger.info(
            "Reranked {} documents, top score: {:.4f}",
            len(ranked_docs),
            ranked_scores[0] if ranked_scores else 0,
        )
        return ranked_docs, ranked_scores

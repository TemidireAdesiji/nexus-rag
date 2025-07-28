"""Core retrieval orchestration pipeline."""

from __future__ import annotations

import time

from loguru import logger

from gateway.clients.data_api import (
    DataServiceClient,
)
from gateway.config import GatewaySettings
from gateway.models import (
    SearchOutcome,
    SearchStrategy,
)
from gateway.retrieval.indexer import DocumentIndexer
from gateway.retrieval.loader import CorpusLoader
from gateway.retrieval.reranker import (
    CrossEncoderReranker,
)
from gateway.retrieval.strategies import (
    StrategyExecutor,
)


class RetrievalPipeline:
    """End-to-end retrieval with indexing + reranking."""

    def __init__(
        self,
        config: GatewaySettings,
        data_client: DataServiceClient | None = None,
        llm: object | None = None,
    ) -> None:
        self._config = config
        self._data_client = data_client
        self._indexer = DocumentIndexer(config)
        self._loader = CorpusLoader()
        self._strategies = StrategyExecutor(
            indexer=self._indexer,
            llm=llm,
            result_limit=config.result_limit,
        )
        self._reranker: CrossEncoderReranker | None
        if config.reranking_enabled:
            self._reranker = CrossEncoderReranker(
                model_name=(config.reranker_model_name),
            )
        else:
            self._reranker = None
        self._warmed = False

    def warm_up(self) -> None:
        """Load corpus and build indexes."""
        docs = []

        if self._data_client is not None:
            api_docs = self._loader.fetch_from_api(
                self._data_client,
            )
            docs.extend(api_docs)

        local_docs = self._loader.scan_directory(
            self._config.upload_dir,
        )
        docs.extend(local_docs)

        if not docs:
            logger.warning(
                "No documents found for indexing",
            )
            self._warmed = True
            return

        chunks = self._indexer.segment_documents(
            docs,
        )
        self._indexer.build_vector_index(chunks)
        self._indexer.build_keyword_index(chunks)
        self._indexer.build_combined_index()
        self._warmed = True

        logger.info(
            "Pipeline warmed: {} docs, {} chunks",
            len(docs),
            len(chunks),
        )

    def search(
        self,
        query: str,
        strategy: SearchStrategy = (SearchStrategy.VECTOR),
    ) -> SearchOutcome:
        """Run a retrieval search."""
        start = time.perf_counter()

        raw_docs = self._strategies.run(
            query,
            strategy,
        )

        scores: list[float] = []
        if self._reranker is not None and raw_docs:
            raw_docs, scores = self._reranker.reorder(
                query,
                raw_docs,
            )
            threshold = self._config.relevance_threshold
            filtered = [
                (doc, score)
                for doc, score in zip(
                    raw_docs,
                    scores,
                    strict=False,
                )
                if score >= threshold
            ]
            if filtered:
                raw_docs = [f[0] for f in filtered]
                scores = [f[1] for f in filtered]

        elapsed = time.perf_counter() - start

        return SearchOutcome(
            documents=raw_docs,
            scores=scores,
            query=query,
            strategy=strategy,
            elapsed_seconds=round(elapsed, 4),
            metadata={
                "chunk_count": (self._indexer.chunk_count),
                "reranked": (self._reranker is not None),
            },
        )

    @property
    def is_warmed_up(self) -> bool:
        """Whether the pipeline is ready."""
        return self._warmed

    @property
    def indexer(self) -> DocumentIndexer:
        """Access the underlying indexer."""
        return self._indexer

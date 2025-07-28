"""Retrieval strategy implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.documents import Document
from langchain_core.output_parsers import (
    StrOutputParser,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from loguru import logger

from gateway.generation.prompts import (
    DECOMPOSITION_TEMPLATE,
    MULTI_QUERY_TEMPLATE,
)
from gateway.models import SearchStrategy

if TYPE_CHECKING:
    from gateway.retrieval.indexer import (
        DocumentIndexer,
    )


class StrategyExecutor:
    """Dispatch queries using different strategies."""

    def __init__(
        self,
        indexer: DocumentIndexer,
        llm: object | None = None,
        result_limit: int = 5,
    ) -> None:
        self._indexer = indexer
        self._llm = llm
        self._limit = result_limit

    def run(
        self,
        query: str,
        strategy: SearchStrategy,
    ) -> list[Document]:
        """Execute the chosen retrieval strategy."""
        dispatch = {
            SearchStrategy.VECTOR: (self._vector_search),
            SearchStrategy.COMBINED: (self._combined_search),
            SearchStrategy.EXPANDED: (self._expanded_search),
            SearchStrategy.DECOMPOSED: (self._decomposed_search),
        }
        handler = dispatch.get(
            strategy,
            self._vector_search,
        )
        results = handler(query)
        logger.info(
            "Strategy {} returned {} results",
            strategy.value,
            len(results),
        )
        return results

    def _vector_search(
        self,
        query: str,
    ) -> list[Document]:
        """Pure vector similarity search."""
        store = self._indexer.vector_store
        if store is None:
            return []
        return store.similarity_search(
            query,
            k=self._limit,
        )

    def _combined_search(
        self,
        query: str,
    ) -> list[Document]:
        """Hybrid vector + keyword search."""
        retriever = self._indexer.combined_retriever
        if retriever is None:
            return self._vector_search(query)
        return retriever.invoke(query)

    def _expanded_search(
        self,
        query: str,
    ) -> list[Document]:
        """Generate query variants, merge results."""
        variants = self._generate_variants(query)
        seen_ids: set[str] = set()
        merged: list[Document] = []

        for variant in variants:
            docs = self._vector_search(variant)
            for doc in docs:
                doc_id = doc.page_content[:100]
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    merged.append(doc)

        return merged[: self._limit * 2]

    def _decomposed_search(
        self,
        query: str,
    ) -> list[Document]:
        """Break query into sub-questions."""
        sub_queries = self._decompose_query(query)
        seen_ids: set[str] = set()
        merged: list[Document] = []

        for sub_q in sub_queries:
            docs = self._vector_search(sub_q)
            for doc in docs:
                doc_id = doc.page_content[:100]
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    merged.append(doc)

        return merged[: self._limit * 2]

    def _generate_variants(
        self,
        query: str,
    ) -> list[str]:
        """Use LLM to produce query variants."""
        if self._llm is None:
            return [query]

        try:
            prompt = ChatPromptTemplate.from_template(
                MULTI_QUERY_TEMPLATE,
            )
            chain = prompt | self._llm | StrOutputParser()
            raw = chain.invoke(
                {"question": query},
            )
            lines = [
                line.strip()
                for line in raw.strip().split("\n")
                if line.strip()
            ]
            return [query, *lines[:3]]
        except Exception:
            logger.warning(
                "Query expansion failed, using original query",
            )
            return [query]

    def _decompose_query(
        self,
        query: str,
    ) -> list[str]:
        """Use LLM to split complex query."""
        if self._llm is None:
            return [query]

        try:
            prompt = ChatPromptTemplate.from_template(
                DECOMPOSITION_TEMPLATE,
            )
            chain = prompt | self._llm | StrOutputParser()
            raw = chain.invoke(
                {"question": query},
            )
            lines = [
                line.strip()
                for line in raw.strip().split("\n")
                if line.strip()
            ]
            return lines[:4] if lines else [query]
        except Exception:
            logger.warning(
                "Query decomposition failed, using original query",
            )
            return [query]

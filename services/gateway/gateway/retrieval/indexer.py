"""Document chunking and vector-store indexing."""

from __future__ import annotations

from pathlib import Path

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import (
    BM25Retriever,
)
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import (
    HuggingFaceEmbeddings,
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from loguru import logger

from gateway.config import GatewaySettings
from gateway.retrieval.loader import CorpusLoader


class DocumentIndexer:
    """Chunks documents and builds retrieval indexes."""

    def __init__(
        self,
        settings: GatewaySettings,
    ) -> None:
        self._settings = settings
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_length,
            chunk_overlap=(settings.chunk_overlap_length),
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )
        self._embeddings = HuggingFaceEmbeddings(
            model_name=(settings.embedding_model_name),
        )
        self._vector_store: Chroma | None = None
        self._bm25: BM25Retriever | None = None
        self._ensemble: EnsembleRetriever | None = None
        self._chunks: list[Document] = []
        self._loader = CorpusLoader()

    def segment_documents(
        self,
        docs: list[Document],
    ) -> list[Document]:
        """Split documents into chunks."""
        chunks = self._splitter.split_documents(
            docs,
        )
        logger.info(
            "Segmented {} docs into {} chunks",
            len(docs),
            len(chunks),
        )
        return chunks

    def build_vector_index(
        self,
        chunks: list[Document],
    ) -> Chroma:
        """Create a ChromaDB vector store."""
        self._vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self._embeddings,
            persist_directory=(self._settings.vector_store_path),
            collection_name=(self._settings.vector_collection),
        )
        logger.info(
            "Built vector index with {} chunks",
            len(chunks),
        )
        return self._vector_store

    def build_keyword_index(
        self,
        chunks: list[Document],
    ) -> BM25Retriever:
        """Create a BM25 keyword retriever."""
        self._bm25 = BM25Retriever.from_documents(
            chunks,
            k=self._settings.result_limit,
        )
        logger.info(
            "Built keyword index with {} chunks",
            len(chunks),
        )
        return self._bm25

    def build_combined_index(
        self,
    ) -> EnsembleRetriever | None:
        """Create ensemble of vector + keyword."""
        if self._vector_store is None or self._bm25 is None:
            logger.warning(
                "Cannot build combined index: missing vector or keyword index",
            )
            return None

        vector_retriever = self._vector_store.as_retriever(
            search_kwargs={
                "k": self._settings.result_limit,
            },
        )
        self._ensemble = EnsembleRetriever(
            retrievers=[
                vector_retriever,
                self._bm25,
            ],
            weights=[0.6, 0.4],
        )
        logger.info("Built combined retriever")
        return self._ensemble

    def append_documents(
        self,
        docs: list[Document],
    ) -> None:
        """Add new documents to existing indexes."""
        chunks = self.segment_documents(docs)
        self._chunks.extend(chunks)

        if self._vector_store is not None:
            self._vector_store.add_documents(chunks)

        if self._bm25 is not None:
            self._bm25 = BM25Retriever.from_documents(
                self._chunks,
                k=self._settings.result_limit,
            )

        if self._ensemble is not None:
            self.build_combined_index()

        logger.info(
            "Appended {} documents ({} chunks)",
            len(docs),
            len(chunks),
        )

    def ingest_file(
        self,
        filepath: str | Path,
    ) -> int:
        """Read, chunk, and index a single file."""
        content = self._loader.parse_file(filepath)
        if not content.strip():
            return 0
        doc = Document(
            page_content=content,
            metadata={
                "source": str(filepath),
                "origin": "upload",
            },
        )
        chunks = self.segment_documents([doc])
        self._chunks.extend(chunks)

        if self._vector_store is not None:
            self._vector_store.add_documents(chunks)
        else:
            self.build_vector_index(chunks)

        if self._bm25 is not None:
            self._bm25 = BM25Retriever.from_documents(
                self._chunks,
                k=self._settings.result_limit,
            )
        else:
            self.build_keyword_index(chunks)

        if self._ensemble is not None:
            self.build_combined_index()

        return len(chunks)

    @property
    def vector_store(self) -> Chroma | None:
        """Access the vector store."""
        return self._vector_store

    @property
    def keyword_retriever(
        self,
    ) -> BM25Retriever | None:
        """Access the BM25 retriever."""
        return self._bm25

    @property
    def combined_retriever(
        self,
    ) -> EnsembleRetriever | None:
        """Access the ensemble retriever."""
        return self._ensemble

    @property
    def chunk_count(self) -> int:
        """Total indexed chunks."""
        return len(self._chunks)

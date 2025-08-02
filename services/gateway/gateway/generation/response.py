"""Response generation using LCEL pipeline."""

from __future__ import annotations

from typing import Any

from langchain_core.documents import Document
from langchain_core.output_parsers import (
    StrOutputParser,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from loguru import logger

from gateway.generation.prompts import (
    ANSWER_TEMPLATE,
)


class AnswerComposer:
    """Generate answers via an LCEL chain."""

    def __init__(
        self,
        llm: object,
        memory_window: int = 8,
    ) -> None:
        self._llm = llm
        self._memory_window = memory_window
        self._prompt = ChatPromptTemplate.from_template(
            ANSWER_TEMPLATE,
        )
        self._chain = (
            self._prompt
            | self._llm  # type: ignore[arg-type]
            | StrOutputParser()
        )

    def compose(
        self,
        query: str,
        retrieved: list[Document] | None = None,
        api_context: str = "",
        api_trace: list[dict[str, Any]] | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        """Produce an answer from all sources."""
        context_text = self._format_documents(
            retrieved or [],
        )
        history_text = self._format_history(
            history or [],
        )

        try:
            answer: str = self._chain.invoke(
                {
                    "context": context_text,
                    "api_context": (api_context or "None available"),
                    "chat_history": (history_text or "No prior conversation"),
                    "question": query,
                },
            )
        except Exception:
            logger.error(
                "LLM invocation failed for query: {}",
                query[:80],
            )
            answer = (
                "I was unable to generate a response "
                "at this time. Please try again."
            )

        return answer.strip()

    @staticmethod
    def _format_documents(
        docs: list[Document],
    ) -> str:
        """Combine document contents for context."""
        if not docs:
            return "No relevant documents found."
        parts: list[str] = []
        for idx, doc in enumerate(docs, 1):
            source = doc.metadata.get(
                "source",
                "unknown",
            )
            parts.append(
                f"[Source {idx}: {source}]\n{doc.page_content}",
            )
        return "\n\n---\n\n".join(parts)

    def _format_history(
        self,
        messages: list[dict[str, Any]],
    ) -> str:
        """Format recent conversation history."""
        recent = messages[-(self._memory_window * 2) :]
        if not recent:
            return ""
        lines: list[str] = []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

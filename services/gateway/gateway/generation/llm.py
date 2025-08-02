"""LLM provider abstraction layer."""

from __future__ import annotations

from langchain_ollama import OllamaLLM
from loguru import logger


class LanguageModel:
    """Wrapper around an Ollama-hosted LLM."""

    def __init__(
        self,
        model_name: str = "llama3",
    ) -> None:
        self._model_name = model_name
        self._llm = OllamaLLM(model=model_name)
        logger.info(
            "Initialised LLM: {}",
            model_name,
        )

    def invoke(self, prompt_text: str) -> str:
        """Send a prompt and return the response."""
        return self._llm.invoke(prompt_text)

    @property
    def model_id(self) -> str:
        """Name of the underlying model."""
        return self._model_name

    @property
    def underlying(self) -> OllamaLLM:
        """Access the raw LangChain LLM object."""
        return self._llm

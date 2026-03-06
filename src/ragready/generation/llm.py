"""LLM factory with Gemini primary + Qwen/Ollama fallback.

Provides LLMWithFallback that tries Gemini Flash first, then falls back
to a local Qwen model via Ollama if the primary fails.
"""

from __future__ import annotations

import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from ragready.core.config import Settings
from ragready.core.exceptions import LLMUnavailableError


class LLMWithFallback:
    """Tries Gemini Flash first, falls back to Qwen via Ollama on failure.

    Wraps two LangChain chat model instances and provides a unified invoke()
    interface with automatic failover. Also supports with_structured_output()
    to propagate JSON schema binding to both models.
    """

    def __init__(self, primary, fallback, logger) -> None:
        self._primary = primary
        self._fallback = fallback
        self._logger = logger
        self._using_fallback = False

    def invoke(self, messages):
        """Invoke primary LLM, fall back to secondary on any error."""
        try:
            result = self._primary.invoke(messages)
            self._using_fallback = False
            return result
        except Exception as e:
            self._logger.warning("primary_llm_failed", error=str(e), fallback="ollama")
            try:
                result = self._fallback.invoke(messages)
                self._using_fallback = True
                return result
            except Exception as fallback_err:
                raise LLMUnavailableError(
                    f"Both LLMs failed. Primary: {e}, Fallback: {fallback_err}"
                ) from fallback_err

    def with_structured_output(self, schema):
        """Return a new LLMWithFallback where both LLMs produce structured output."""
        return LLMWithFallback(
            primary=self._primary.with_structured_output(schema, method="json_schema"),
            fallback=self._fallback.with_structured_output(schema),
            logger=self._logger,
        )

    @property
    def is_using_fallback(self) -> bool:
        """Whether the last invocation used the fallback LLM."""
        return self._using_fallback


def create_llm(settings: Settings) -> LLMWithFallback:
    """Factory: create Gemini Flash primary + Qwen Ollama fallback.

    Args:
        settings: Application settings with LLM configuration.

    Returns:
        LLMWithFallback instance ready for invocation.
    """
    primary = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        temperature=settings.temperature,
        google_api_key=settings.google_api_key,
        max_retries=settings.llm_max_retries,
    )
    fallback = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.temperature,
    )
    return LLMWithFallback(primary=primary, fallback=fallback, logger=structlog.get_logger())

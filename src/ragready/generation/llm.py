"""LLM factory with Gemini primary and OpenRouter/Gemini fallback.

Provides LLMWrapper that tries Gemini Flash. If it fails due to rate limit
or other errors, it logs the downtime and attempts to use OpenRouter.
If all fail, it raises an error saying we are working on offline model integration.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
import structlog
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from ragready.core.config import Settings
from ragready.core.exceptions import LLMUnavailableError


class _GeminiUnavailableStub:
    """Stub that raises on invoke when Gemini API key is not configured."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    def invoke(self, messages):
        raise LLMUnavailableError(self._reason)

    def with_structured_output(self, schema, **kwargs):
        return self


def _log_downtime(error_msg: str, fallback_used: bool = False):
    """Log the downtime to a history file."""
    try:
        data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, "downtime.json")
        
        status_msg = "Attempted fallback to OpenRouter." if fallback_used else "No fallback available. We are working on getting an offline model which takes time. Please try again after some time."
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(error_msg),
            "message": status_msg
        }
        
        history = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        history.append(entry)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
            
    except Exception as e:
        logger = structlog.get_logger()
        logger.error("failed_to_log_downtime", error=str(e))


class LLMWrapper:
    """Tries Gemini Flash. Fails over to OpenRouter if configured."""

    def __init__(self, primary: Any, fallback: Any, logger: Any, settings: Settings) -> None:
        self._primary = primary
        self._fallback = fallback
        self._logger = logger
        self._settings = settings

    def invoke(self, messages: Any) -> Any:
        """Invoke primary LLM, fail over to fallback if available."""
        try:
            return self._primary.invoke(messages)
        except Exception as e:
            self._logger.warning("primary_llm_failed", error=str(e))
            if self._fallback and not isinstance(self._fallback, _GeminiUnavailableStub):
                try:
                    self._logger.info("using_openrouter_fallback")
                    _log_downtime(str(e), fallback_used=True)
                    return self._fallback.invoke(messages)
                except Exception as ef:
                    self._logger.error("fallback_llm_failed", error=str(ef))
            
            _log_downtime(str(e), fallback_used=False)
            raise LLMUnavailableError(
                "We are working on getting an offline model which takes time. Please try again after some time."
            ) from e

    async def astream(self, messages: Any) -> AsyncIterator[Any]:
        """Async stream with fallback support."""
        try:
            async for chunk in self._primary.astream(messages):
                yield chunk
        except Exception as e:
            self._logger.warning("primary_llm_stream_failed", error=str(e))
            if self._fallback and not isinstance(self._fallback, _GeminiUnavailableStub):
                try:
                    self._logger.info("using_openrouter_fallback_stream")
                    _log_downtime(str(e), fallback_used=True)
                    async for chunk in self._fallback.astream(messages):
                        yield chunk
                except Exception as ef:
                    self._logger.error("fallback_llm_stream_failed", error=str(ef))
                    raise
            else:
                _log_downtime(str(e), fallback_used=False)
                raise LLMUnavailableError(
                    "We are working on getting an offline model which takes time. Please try again after some time."
                ) from e

    def with_structured_output(self, schema: Any, **kwargs: Any) -> LLMWrapper:
        """Return a new LLMWrapper where both models produce structured output."""
        primary_structured = self._primary.with_structured_output(
            schema, **kwargs
        ) if not isinstance(self._primary, _GeminiUnavailableStub) else self._primary

        fallback_structured = None
        if self._fallback and not isinstance(self._fallback, _GeminiUnavailableStub):
            fallback_structured = self._fallback.with_structured_output(
                schema, **kwargs
            )

        return LLMWrapper(
            primary=primary_structured,
            fallback=fallback_structured,
            logger=self._logger,
            settings=self._settings,
        )

    @property
    def is_using_fallback(self) -> bool:
        return False


def create_llm(settings: Settings) -> LLMWrapper:
    """Factory: create Gemini Flash primary with OpenRouter fallback.

    Args:
        settings: Application settings with LLM configuration.

    Returns:
        LLMWrapper instance ready for invocation.
    """
    logger = structlog.get_logger()

    # 1. Primary: Gemini
    primary = None
    if settings.google_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            primary = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                temperature=settings.temperature,
                google_api_key=settings.google_api_key,
                max_retries=settings.llm_max_retries,
            )
            logger.info("gemini_primary_configured", model=settings.llm_model)
        except Exception as e:
            logger.warning("gemini_init_failed", error=str(e))
            primary = _GeminiUnavailableStub(reason=f"Gemini init failed: {e}")
    else:
        logger.info("gemini_api_key_not_set")
        primary = _GeminiUnavailableStub(
            reason="Google API key not configured (set RAGREADY_GOOGLE_API_KEY)"
        )

    # 2. Fallback: OpenRouter
    fallback = None
    if settings.openrouter_api_key:
        try:
            from langchain_openai import ChatOpenAI
            fallback = ChatOpenAI(
                model=settings.openrouter_model,
                openai_api_key=settings.openrouter_api_key,
                openai_api_base=settings.openrouter_base_url,
                temperature=settings.temperature,
                max_retries=settings.llm_max_retries,
            )
            logger.info("openrouter_fallback_configured", model=settings.openrouter_model)
        except Exception as e:
            logger.warning("openrouter_init_failed", error=str(e))
            fallback = _GeminiUnavailableStub(reason=f"OpenRouter init failed: {e}")
    else:
        logger.info("openrouter_api_key_not_set")
        fallback = _GeminiUnavailableStub(
            reason="OpenRouter API key not configured (set RAGREADY_OPENROUTER_API_KEY)"
        )

    return LLMWrapper(primary=primary, fallback=fallback, logger=logger, settings=settings)

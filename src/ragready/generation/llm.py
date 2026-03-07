"""LLM factory with Gemini primary.

Provides LLMWrapper that tries Gemini Flash. If it fails due to rate limit
or other errors, it logs the downtime and raises an error saying we are
working on offline model integration.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
import structlog

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


def _log_downtime(error_msg: str):
    """Log the downtime to a history file."""
    try:
        data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, "downtime.json")
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(error_msg),
            "message": "We are working on getting an offline model which takes time. Please try again after some time."
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
    """Tries Gemini Flash. Fails with a specific message on any error."""

    def __init__(self, primary, logger) -> None:
        self._primary = primary
        self._logger = logger
        self._using_fallback = False

    def invoke(self, messages):
        """Invoke primary LLM, fail with explicit message on error."""
        try:
            return self._primary.invoke(messages)
        except Exception as e:
            self._logger.warning("primary_llm_failed", error=str(e))
            _log_downtime(str(e))
            raise LLMUnavailableError(
                "We are working on getting an offline model which takes time. Please try again after some time."
            ) from e

    def with_structured_output(self, schema):
        """Return a new LLMWrapper where LLM produces structured output."""
        primary_structured = self._primary.with_structured_output(
            schema, method="json_schema"
        ) if not isinstance(self._primary, _GeminiUnavailableStub) else self._primary
        return LLMWrapper(
            primary=primary_structured,
            logger=self._logger,
        )

    @property
    def is_using_fallback(self) -> bool:
        return False


def create_llm(settings: Settings) -> LLMWrapper:
    """Factory: create Gemini Flash primary wrapper.

    Args:
        settings: Application settings with LLM configuration.

    Returns:
        LLMWrapper instance ready for invocation.
    """
    logger = structlog.get_logger()

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

    return LLMWrapper(primary=primary, logger=logger)

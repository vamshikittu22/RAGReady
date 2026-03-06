"""Phoenix OTEL tracing setup for RAGReady.

Initializes Arize Phoenix tracing with OpenInference LangChain instrumentation.
Tracing is optional and non-blocking — the app works without Phoenix.
"""

import structlog

from ragready.core.config import Settings

logger = structlog.get_logger()


def setup_tracing(settings: Settings) -> None:
    """Initialize Arize Phoenix tracing for the RAG pipeline.

    Uses arize-phoenix-otel for the OTEL tracer and
    openinference-instrumentation-langchain to auto-instrument LangChain.

    If Phoenix server is unreachable, logs a warning and continues
    without tracing (non-blocking).

    IMPORTANT: This function must be called BEFORE any LangChain
    invocations to ensure spans are captured.
    """
    try:
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor

        tracer_provider = register(
            project_name="ragready",
            endpoint=settings.phoenix_endpoint,
        )
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info(
            "phoenix_tracing_enabled",
            endpoint=settings.phoenix_endpoint,
        )
    except ImportError as e:
        logger.warning(
            "phoenix_tracing_unavailable",
            reason="Required packages not installed",
            error=str(e),
            hint="Install: pip install arize-phoenix-otel openinference-instrumentation-langchain",
        )
    except Exception as e:
        logger.warning(
            "phoenix_tracing_failed",
            reason="Could not connect to Phoenix server",
            error=str(e),
            hint=f"Start Phoenix: docker run -d -p 6006:6006 arizephoenix/phoenix:latest",
        )

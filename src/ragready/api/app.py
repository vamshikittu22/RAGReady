"""FastAPI application factory for RAGReady.

Creates a fully-wired FastAPI app with CORS, latency logging middleware,
route registration, and optional Phoenix tracing via lifespan.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ragready.api.dependencies import get_settings
from ragready.api.middleware import LatencyLoggingMiddleware
from ragready.api.routes import documents, evaluate, health, query
from ragready.observability.tracing import setup_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize tracing on startup."""
    settings = get_settings()
    if settings.phoenix_enabled:
        setup_tracing(settings)
    yield
    # Shutdown: cleanup if needed


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully-configured FastAPI instance with all routes and middleware.
    """
    app = FastAPI(
        title="RAGReady",
        description="Production-grade RAG system with hybrid retrieval and citation-enforced generation",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware (order matters: CORS first, then latency logging)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LatencyLoggingMiddleware)

    # Routes
    app.include_router(query.router)
    app.include_router(documents.router)
    app.include_router(health.router)
    app.include_router(evaluate.router)

    return app

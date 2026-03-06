"""FastAPI REST API for RAGReady.

Provides endpoints for querying, document management, and health checks.
"""

from ragready.api.app import create_app

__all__ = ["create_app"]

"""Health check endpoint: GET /health."""

import json
import os
from fastapi import APIRouter, Depends

from ragready.api.dependencies import get_pipeline, get_settings
from ragready.core.config import Settings
from ragready.ingestion.pipeline import IngestionPipeline

router = APIRouter(tags=["System"])


@router.get("/health")
def health_check(
    settings: Settings = Depends(get_settings),
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """System health check.

    Returns system status including LLM model configuration,
    document count, and Phoenix tracing status.
    """
    docs = pipeline.list_documents()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "llm_model": settings.llm_model,
        "document_count": len(docs),
        "phoenix_enabled": settings.phoenix_enabled,
    }


@router.get("/downtime-history")
def downtime_history():
    """Return the history of when the LLM failed."""
    data_dir = os.path.join(os.getcwd(), "data")
    file_path = os.path.join(data_dir, "downtime.json")
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

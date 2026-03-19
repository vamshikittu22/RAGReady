"""Document management endpoints: upload, list, delete."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ragready.api.dependencies import get_pipeline
from ragready.core.exceptions import DocumentNotFoundError
from ragready.ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt", ".html"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    custom_name: str | None = Form(None),
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """Upload a document for ingestion into the RAG pipeline.

    Accepts .pdf, .md, .txt, and .html files. Returns document metadata
    including document_id and chunk_count.
    """
    # Use custom_name if provided, otherwise file.filename
    final_name = custom_name.strip() if custom_name and custom_name.strip() else (file.filename or "unknown.txt")
    
    # Validate file type
    suffix = Path(final_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Save to temp directory with the exact filename so pipeline gets the correct name
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_path = Path(temp_dir) / final_name
        content = await file.read()
        tmp_path.write_bytes(content)

        try:
            doc = pipeline.ingest(tmp_path)
            return {
                "document_id": doc.document_id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "chunk_count": doc.chunk_count,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@router.get("/")
def list_documents(
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """List all ingested documents."""
    docs = pipeline.list_documents()
    return {"documents": [doc.model_dump() for doc in docs], "count": len(docs)}


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """Delete a document and its chunks from all indexes."""
    deleted = pipeline.delete(document_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Document not found: {document_id}"
        )
    return {"deleted": document_id}

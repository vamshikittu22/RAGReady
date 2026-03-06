"""Document management endpoints: upload, list, delete."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ragready.api.dependencies import get_pipeline
from ragready.core.exceptions import DocumentNotFoundError
from ragready.ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt", ".html"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """Upload a document for ingestion into the RAG pipeline.

    Accepts .pdf, .md, .txt, and .html files. Returns document metadata
    including document_id and chunk_count.
    """
    # Validate file type
    suffix = Path(file.filename).suffix.lower() if file.filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Save to temp file and ingest
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

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
    finally:
        tmp_path.unlink(missing_ok=True)


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

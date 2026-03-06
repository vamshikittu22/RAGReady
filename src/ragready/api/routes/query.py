"""Query endpoint: POST /query for RAG question answering."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ragready.api.dependencies import get_rag_chain
from ragready.core.exceptions import GenerationError, LLMUnavailableError
from ragready.generation.chain import RAGChain
from ragready.generation.models import QueryResponse, QueryResult, RefusalResponse

router = APIRouter(tags=["Query"])


class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""

    question: str = Field(
        ..., min_length=1, max_length=1000, description="The question to answer"
    )


@router.post("/query", response_model=QueryResponse | RefusalResponse)
def query_documents(
    request: QueryRequest,
    rag_chain: RAGChain = Depends(get_rag_chain),
) -> QueryResult:
    """Ask a question and get a grounded, cited answer.

    Returns a structured answer with citations if sufficient evidence exists,
    or a refusal with reason if evidence is insufficient.
    """
    try:
        result = rag_chain.query(request.question)
        return result
    except LLMUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except GenerationError as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {e}")

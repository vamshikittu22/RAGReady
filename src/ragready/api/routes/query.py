"""Query endpoint: POST /query for RAG question answering."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import asyncio
from structlog import get_logger

from ragready.api.dependencies import get_rag_chain
from ragready.core.exceptions import GenerationError, LLMUnavailableError
from ragready.generation.chain import RAGChain
from ragready.generation.models import QueryResponse, QueryResult, RefusalResponse

router = APIRouter(tags=["Query"])
logger = get_logger()


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
    """Ask a question and get a grounded, cited answer."""
    try:
        result = rag_chain.query(request.question)
        return result
    except LLMUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except GenerationError as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {e}")


async def generate_stream(question: str, rag_chain: RAGChain):
    """Generate streaming response for a question."""
    try:
        # 1. Retrieve context
        chunks = rag_chain._retriever.retrieve(question)
        
        # 2. Pre-LLM refusal checks
        if not chunks:
            refusal = RefusalResponse(
                reason="No relevant documents found to answer the question",
                confidence=0.0,
            ).model_dump()
            yield f"data: {json.dumps({'type': 'refusal', 'data': refusal})}\n\n"
            return
        
        max_score = max(c.score for c in chunks)
        settings = rag_chain._settings
        if max_score < settings.confidence_threshold:
            refusal = RefusalResponse(
                reason="Retrieved evidence is insufficient to answer confidently",
                confidence=max_score,
            ).model_dump()
            yield f"data: {json.dumps({'type': 'refusal', 'data': refusal})}\n\n"
            return
        
        # 3. Build Citations (from retrieval)
        # ScoredChunk wraps a Chunk: c.chunk.text, c.chunk.metadata.source_document, etc.
        citations = []
        for c in chunks[:5]:
            citations.append({
                "chunk_text": c.chunk.text[:500],
                "document_name": c.chunk.metadata.source_document,
                "page_number": c.chunk.metadata.page_number,
                "relevance_score": c.score,
            })
        
        # 4. Stream Answer
        from ragready.generation.prompts import build_prompt
        messages = build_prompt(question, chunks)
        
        full_answer = ""
        try:
            # We use the raw LLM for streaming text to avoid structured output complexity during streaming
            # The wrapper will handle fallback automatically
            async for chunk in rag_chain._llm.astream(messages):
                content = ""
                if isinstance(chunk, str):
                    content = chunk
                elif hasattr(chunk, 'content'):
                    content = chunk.content
                
                if content:
                    full_answer += content
                    yield f"data: {json.dumps({'type': 'token', 'data': content})}\n\n"
            
            # 5. Finalize
            response_data = {
                "answer": full_answer,
                "confidence": max_score * 0.95,
                "citations": citations,
                "refused": False
            }
            yield f"data: {json.dumps({'type': 'done', 'data': response_data})}\n\n"

        except Exception as e:
            logger.warning("streaming_failed_trying_invoke", error=str(e))
            # Fallback to non-streaming structured output for the final result if possible
            structured_llm = rag_chain._llm.with_structured_output(QueryResponse)
            response = structured_llm.invoke(messages)
            yield f"data: {json.dumps({'type': 'token', 'data': response.answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'data': response.model_dump()})}\n\n"
            
    except Exception as e:
        logger.error("stream_generation_failed", error=str(e))
        yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"


@router.post("/query/stream")
async def query_documents_stream(
    request: QueryRequest,
    rag_chain: RAGChain = Depends(get_rag_chain),
):
    """Ask a question and get a streaming response with SSE."""
    return StreamingResponse(
        generate_stream(request.question, rag_chain),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

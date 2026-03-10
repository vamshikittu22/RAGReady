"""Query endpoint: POST /query for RAG question answering."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import asyncio

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


async def generate_stream(question: str, rag_chain: RAGChain):
    """Generate streaming response for a question.
    
    Yields SSE tokens with the answer as it's being generated.
    """
    try:
        # First, retrieve chunks (non-streaming)
        chunks = rag_chain._retriever.retrieve(question)
        
        # Pre-LLM refusal check
        if not chunks:
            refusal = RefusalResponse(
                reason="No relevant documents found to answer the question",
                confidence=0.0,
            )
            yield f"data: {json.dumps({'type': 'refusal', 'data': refusal.model_dump()})}\n\n"
            return
        
        max_score = max(c.score for c in chunks)
        settings = rag_chain._settings
        if max_score < settings.confidence_threshold:
            refusal = RefusalResponse(
                reason="Retrieved evidence is insufficient to answer confidently",
                confidence=max_score,
            )
            yield f"data: {json.dumps({'type': 'refusal', 'data': refusal.model_dump()})}\n\n"
            return
        
        # Get citations (these come from retrieved chunks, not streamed)
        from ragready.generation.prompts import build_prompt
        messages = build_prompt(question, chunks)
        
        # For streaming, we'll stream the answer field character by character
        # Use the LLM in streaming mode if supported
        try:
            structured_llm = rag_chain._llm.with_structured_output(QueryResponse)
            
            # Check if the underlying LLM supports streaming
            if hasattr(structured_llm._primary, 'stream'):
                # Stream token by token
                full_answer = ""
                async for chunk in structured_llm._primary.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        full_answer += chunk.content
                        yield f"data: {json.dumps({'type': 'token', 'data': chunk.content})}\n\n"
                
                # After streaming completes, get citations from prompt
                citations = []
                for c in chunks[:5]:  # Top 5 citations
                    citations.append({
                        "text": c.text[:500],  # Truncate for response
                        "document_name": c.document_name,
                        "page": c.page,
                        "score": c.score,
                    })
                
                # Send final message with complete response
                response_data = {
                    "answer": full_answer,
                    "confidence": max_score * 0.9,  # Estimate based on retrieval
                    "citations": citations,
                }
                yield f"data: {json.dumps({'type': 'done', 'data': response_data})}\n\n"
            else:
                # LLM doesn't support streaming - generate complete response
                response = structured_llm.invoke(messages)
                # Stream the answer as a single chunk (fallback)
                yield f"data: {json.dumps({'type': 'token', 'data': response.answer})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'data': response.model_dump()})}\n\n"
                
        except Exception as e:
            # If streaming fails, fall back to non-streaming
            structured_llm = rag_chain._llm.with_structured_output(QueryResponse)
            response = structured_llm.invoke(messages)
            yield f"data: {json.dumps({'type': 'token', 'data': response.answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'data': response.model_dump()})}\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"


@router.post("/query/stream")
async def query_documents_stream(
    request: QueryRequest,
    rag_chain: RAGChain = Depends(get_rag_chain),
):
    """Ask a question and get a streaming response with SSE.
    
    Returns Server-Sent Events (SSE) stream with:
    - type: 'token' -> incremental text chunks
    - type: 'done' -> final complete response
    - type: 'refusal' -> system refused to answer
    - type: 'error' -> error occurred
    """
    return StreamingResponse(
        generate_stream(request.question, rag_chain),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )

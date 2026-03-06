"""Pydantic models for RAG generation structured output.

These models define the LLM output schema for citation-enforced generation.
Used with LangChain's with_structured_output() to guarantee JSON conformance.
"""

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A citation linking an answer claim to a source chunk."""

    chunk_text: str = Field(description="Exact text from the source chunk used to support the answer")
    document_name: str = Field(description="Source document filename")
    page_number: int | None = Field(default=None, description="Page number if available")
    relevance_score: float = Field(description="Chunk retrieval relevance score")


class QueryResponse(BaseModel):
    """Structured response from the RAG chain with citations."""

    answer: str = Field(description="Answer grounded in the provided context chunks")
    citations: list[Citation] = Field(description="Source citations supporting the answer")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0 based on evidence quality"
    )


class RefusalResponse(BaseModel):
    """Response when the system refuses to answer due to insufficient evidence."""

    refused: bool = Field(default=True, description="Always True for refusal responses")
    reason: str = Field(description="Explanation of why the system cannot answer")
    confidence: float = Field(
        ge=0.0, le=1.0, description="The confidence score that was below threshold"
    )


QueryResult = QueryResponse | RefusalResponse

"""RAG generation chain: query -> retrieve -> check evidence -> generate -> validate.

Orchestrates the full RAG pipeline from user question to cited answer,
with pre-LLM refusal gating based on retrieval quality.
"""

from __future__ import annotations

import structlog

from ragready.core.config import Settings
from ragready.core.models import ScoredChunk
from ragready.generation.llm import LLMWrapper, create_llm
from ragready.generation.models import QueryResponse, QueryResult, RefusalResponse
from ragready.generation.prompts import build_prompt


class RAGChain:
    """Orchestrates: query -> retrieve -> check evidence -> generate -> validate.

    Two-stage confidence check:
    1. Pre-LLM: Check if max retrieval score meets threshold (saves tokens on hopeless queries)
    2. Post-LLM: Return the LLM's self-reported confidence in the response

    Args:
        retriever: HybridRetriever from Phase 1.
        llm: LLMWrapper from llm.py.
        settings: App settings (confidence_threshold, etc.).
    """

    def __init__(self, retriever, llm: LLMWrapper, settings: Settings) -> None:
        self._retriever = retriever
        self._llm = llm
        self._settings = settings
        self._logger = structlog.get_logger()

    def query(self, question: str) -> QueryResult:
        """Execute the full RAG pipeline for a question.

        Steps:
        1. Retrieve chunks via HybridRetriever
        2. Check retrieval quality (pre-LLM refusal gate)
        3. Build grounding prompt
        4. Generate structured response via LLM
        5. Return QueryResponse or RefusalResponse

        Args:
            question: The user's question.

        Returns:
            QueryResponse with answer and citations, or RefusalResponse
            if evidence is insufficient.
        """
        # Step 1: Retrieve
        chunks: list[ScoredChunk] = self._retriever.retrieve(question)

        # Step 2: Pre-LLM refusal check
        if not chunks:
            self._logger.info("query_refused", reason="no_chunks_retrieved", max_score=0.0)
            return RefusalResponse(
                reason="No relevant documents found to answer the question",
                confidence=0.0,
            )

        max_score = max(c.score for c in chunks)
        if max_score < self._settings.confidence_threshold:
            self._logger.info(
                "query_refused", reason="insufficient_evidence", max_score=max_score
            )
            return RefusalResponse(
                reason="Retrieved evidence is insufficient to answer confidently",
                confidence=max_score,
            )

        # Step 3: Build prompt
        messages = build_prompt(question, chunks)

        # Step 4: Generate with structured output
        structured_llm = self._llm.with_structured_output(QueryResponse)
        response = structured_llm.invoke(messages)

        # Step 5: Return
        self._logger.info(
            "query_answered",
            confidence=response.confidence,
            citations=len(response.citations),
        )
        return response


def create_rag_chain(retriever, settings: Settings | None = None) -> RAGChain:
    """Factory: construct a fully-wired RAGChain.

    Args:
        retriever: A HybridRetriever instance for chunk retrieval.
        settings: Optional Settings override (uses defaults if None).

    Returns:
        A ready-to-use RAGChain.
    """
    settings = settings or Settings()
    llm = create_llm(settings)
    return RAGChain(retriever=retriever, llm=llm, settings=settings)

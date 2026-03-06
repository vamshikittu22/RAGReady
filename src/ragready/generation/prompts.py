"""Grounding prompt templates for citation-enforced generation.

Defines the system prompt and message builder that enforce the LLM
to ground all claims in retrieved context chunks with proper citations.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from ragready.core.models import ScoredChunk

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided context.

Rules:
1. ONLY use information from the provided context chunks to answer
2. For each claim in your answer, cite the specific chunk(s) that support it
3. If the context doesn't contain enough information to answer confidently, set confidence below 0.5
4. Never make up information not present in the context
5. Report your confidence (0.0 to 1.0) based on how well the context supports your answer
6. Each citation must reference a real chunk from the provided context"""


def build_prompt(query: str, chunks: list[ScoredChunk]) -> list:
    """Build LangChain message list from query and retrieved chunks.

    Formats each chunk as:
    [Chunk N] (source: {document}, page: {page}, score: {score:.4f})
    {text}

    Args:
        query: The user's question.
        chunks: Retrieved chunks with scores from hybrid retrieval.

    Returns:
        List of [SystemMessage, HumanMessage] for LLM invocation.
    """
    context_parts = []
    for i, scored_chunk in enumerate(chunks, 1):
        chunk = scored_chunk.chunk
        page = chunk.metadata.page_number if chunk.metadata.page_number is not None else "N/A"
        context_parts.append(
            f"[Chunk {i}] (source: {chunk.metadata.source_document}, "
            f"page: {page}, score: {scored_chunk.score:.4f})\n"
            f"{chunk.text}"
        )

    context_block = "\n\n".join(context_parts)

    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Context:\n{context_block}\n\n"
                f"Question: {query}\n\n"
                f"Provide your answer with citations from the context above."
            )
        ),
    ]

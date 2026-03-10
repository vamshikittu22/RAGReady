import traceback
import sys
import os

# Add src to python path just in case
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    print("Checking settings...")
    from ragready.core.config import Settings
    settings = Settings()
    print("Settings loaded.")

    print("Checking Ingestion Pipeline...")
    from ragready.ingestion.pipeline import create_pipeline
    pipeline = create_pipeline(settings)
    print("Pipeline loaded.")

    print("Checking LLM Wrapper...")
    from ragready.generation.llm import create_llm
    llm = create_llm(settings)
    print("LLM loaded.")

    print("Checking RAG Chain...")
    from ragready.generation.chain import create_rag_chain
    from ragready.retrieval.hybrid import create_retriever
    retriever = create_retriever(chroma=pipeline.chroma, bm25=pipeline.bm25, settings=settings)
    chain = create_rag_chain(retriever=retriever, settings=settings)
    print("Chain loaded.")

    print("Checking FastAPI App...")
    from ragready.api.app import create_app
    app = create_app()
    print("App created successfully.")

except Exception:
    traceback.print_exc()
    sys.exit(1)

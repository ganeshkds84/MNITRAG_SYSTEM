import re
from functools import lru_cache

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.runnables import Runnable, RunnableLambda

from config.config import (
    BM25_WEIGHT,
    TOP_K_RESULTS,
    USE_HYBRID_RETRIEVAL,
    VECTOR_WEIGHT,
)
from rag.vectordb import get_vector_store

TOKEN_PATTERN = re.compile(r"\w+")


def bm25_tokenize(text: str) -> list[str]:
    """
    Lowercase word tokenizer for BM25 (the default only splits on
    whitespace and is case-sensitive, so "Fee" != "fee,").
    """
    return TOKEN_PATTERN.findall(text.lower())


@lru_cache(maxsize=1)
def get_bm25_retriever() -> BM25Retriever | None:
    """
    Build the BM25 index once from all chunks stored in Chroma and cache it.
    Restart the app after re-running ingestion to rebuild it.

    Returns:
        BM25Retriever, or None if the vector store is empty
    """
    data = get_vector_store().get(include=["documents", "metadatas"])

    documents = [
        Document(page_content=text, metadata=meta or {})
        for text, meta in zip(data["documents"], data["metadatas"])
    ]

    if not documents:
        return None

    return BM25Retriever.from_documents(
        documents,
        preprocess_func=bm25_tokenize,
    )


def get_retriever(k: int=TOP_K_RESULTS) -> Runnable:
    """
    Create a retriever over the indexed chunks.

    Uses hybrid retrieval (BM25 + vector, fused with weighted reciprocal
    rank) when USE_HYBRID_RETRIEVAL is True, otherwise vector search only.

    Args:
        k :Number of chunks to retrieve

    Returns:
        Runnable that takes a question and returns up to k Documents
    """
    vectorstore=get_vector_store()

    vector_retriever=vectorstore.as_retriever(
        search_type='similarity',
        search_kwargs={"k":k}
    )

    bm25_retriever=get_bm25_retriever() if USE_HYBRID_RETRIEVAL else None

    if bm25_retriever is None:
        return vector_retriever

    # Shallow copy so the cached index is shared but k can differ per call
    bm25_retriever=bm25_retriever.model_copy(update={"k":k})

    ensemble=EnsembleRetriever(
        retrievers=[bm25_retriever,vector_retriever],
        weights=[BM25_WEIGHT,VECTOR_WEIGHT]
    )

    # EnsembleRetriever returns the union of both lists; keep the top k
    return ensemble | RunnableLambda(lambda docs: docs[:k])

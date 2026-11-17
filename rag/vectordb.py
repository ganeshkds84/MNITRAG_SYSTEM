from langchain_chroma import Chroma
import shutil
import os

from config.config import VECTOR_DB_DIRECTORY
from rag.embedding import get_embedding_model

def get_vector_store():
    
    embedding_model=get_embedding_model()
    vector_store=Chroma(
        persist_directory=VECTOR_DB_DIRECTORY,
        embedding_function=embedding_model
    )
    
    return vector_store

def get_vector_store_stats() -> dict:
    """
    Return basic statistics of the persisted vector store.

    Returns:
        {"chunks": number of stored chunks,
         "sources": number of distinct source files}
        Both are 0 if the store is missing or empty.
    """
    if not os.path.isdir(VECTOR_DB_DIRECTORY):
        return {"chunks": 0, "sources": 0}

    # No embedding function needed just to read metadata
    vector_store = Chroma(persist_directory=VECTOR_DB_DIRECTORY)
    data = vector_store.get(include=["metadatas"])

    metadatas = data.get("metadatas") or []
    sources = {
        meta.get("source")
        for meta in metadatas
        if meta and meta.get("source")
    }

    return {"chunks": len(metadatas), "sources": len(sources)}

def clear_vector_store():
    
    if os.path.exists(VECTOR_DB_DIRECTORY):
        shutil.rmtree(VECTOR_DB_DIRECTORY)
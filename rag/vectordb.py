from langchain_chroma import Chroma
import shutil
import os

from config.config import VECTOR_DB_DIRECTORY
from rag.embedding import get_embedding_model

def get_vector_store(persist_directory: str | None = None):
    """
    Open the Chroma vector store.

    Args:
        persist_directory: Store folder (default: VECTOR_DB_DIRECTORY)
    """
    embedding_model=get_embedding_model()
    vector_store=Chroma(
        persist_directory=persist_directory or VECTOR_DB_DIRECTORY,
        embedding_function=embedding_model
    )

    return vector_store

def get_vector_store_version(persist_directory: str | None = None) -> tuple:
    """
    Identify the current contents of the store, used as a cache key so that
    caches (e.g. the BM25 index) are rebuilt after re-ingestion.

    Returns:
        (directory, chunk count, modification time of chroma.sqlite3)
    """
    directory = persist_directory or VECTOR_DB_DIRECTORY
    sqlite_path = os.path.join(directory, "chroma.sqlite3")

    if not os.path.exists(sqlite_path):
        return (directory, 0, 0.0)

    count = Chroma(persist_directory=directory)._collection.count()

    return (directory, count, os.path.getmtime(sqlite_path))

def get_vector_store_stats(persist_directory: str | None = None) -> dict:
    """
    Return basic statistics of the persisted vector store.

    Returns:
        {"chunks": number of stored chunks,
         "sources": number of distinct source files}
        Both are 0 if the store is missing or empty.
    """
    directory = persist_directory or VECTOR_DB_DIRECTORY

    if not os.path.isdir(directory):
        return {"chunks": 0, "sources": 0}

    # No embedding function needed just to read metadata
    vector_store = Chroma(persist_directory=directory)
    data = vector_store.get(include=["metadatas"])

    metadatas = data.get("metadatas") or []
    sources = {
        meta.get("source")
        for meta in metadatas
        if meta and meta.get("source")
    }

    return {"chunks": len(metadatas), "sources": len(sources)}

def clear_vector_store(persist_directory: str | None = None):

    directory = persist_directory or VECTOR_DB_DIRECTORY

    if os.path.exists(directory):
        shutil.rmtree(directory)

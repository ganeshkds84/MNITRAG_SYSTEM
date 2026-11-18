from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from config.config import EMBEDDING_MODEL

@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the embedding model once and reuse it (loading takes seconds).
    """
    embeddings=HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )
    
    return embeddings
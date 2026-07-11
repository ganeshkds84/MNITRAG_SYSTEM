from langchain_core.vectorstores import VectorStoreRetriever

from rag.vectordb import get_vector_store

def get_retriever(k: int=3)->VectorStoreRetriever:
    """
    Create a retriever from ChromaDB

    Args:
        k :Number of chunks to retrieve

    Returns:
        Langchain retriever
    """
    vectorstore=get_vector_store()
    
    retriever=vectorstore.as_retriever(
        search_type='similarity',
        search_kwargs={"k":k}
    )
    
    return retriever

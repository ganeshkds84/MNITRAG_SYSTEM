from dataclasses import dataclass

@dataclass
class RAGResponse:
    """
    Standard response object for the RAG pipeline.
    """
    
    answer:str
    sources: list[dict]
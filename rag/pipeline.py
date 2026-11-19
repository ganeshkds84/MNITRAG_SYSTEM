from langchain_core.documents import Document

from config.config import TOP_K_RESULTS
from rag.llm import get_llm
from rag.retriever import get_retriever
from rag.prompt_builder import (
    format_context,
    get_rag_prompt
)
from rag.schemas import RAGResponse

def retrieve_documents(
    question:str,
    k: int=TOP_K_RESULTS,
    hybrid: bool | None=None,
    persist_directory: str | None=None,
)->list[Document]:
    """
    Retrieve the chunks used as context for a question.

    Args:
        question: User question
        k: Number of retrieved chunks
        hybrid: BM25 + vector retrieval (default: USE_HYBRID_RETRIEVAL)
        persist_directory: Vector store folder (default: VECTOR_DB_DIRECTORY)
    """
    retriever=get_retriever(
        k=k,
        hybrid=hybrid,
        persist_directory=persist_directory
    )

    return retriever.invoke(question)

def get_sources(documents: list[Document])->list[dict]:
    """
    Unique source entries (file + page) of the retrieved chunks.
    """
    sources=[]

    for doc in documents:
        source_info={
            'source':doc.metadata.get(
                'source',
                'Unknown'
            ),
            'file_name':doc.metadata.get(
                'file_name',
                'Unknown'
            ),
            'page':doc.metadata.get(
                'page',
                'Unknown'
            ),
            'page_label':doc.metadata.get(
                'page_label',
                'Unknown'
            ),
            'category':doc.metadata.get(
                'category',
                'unknown'
            ),
            'doc_year':doc.metadata.get(
                'doc_year',
                'unknown'
            )
        }

        if source_info not in sources:
            sources.append(source_info)

    return sources

def generate_answer(
    question:str,
    documents: list[Document],
)->RAGResponse:
    """
    Generate an answer from already retrieved chunks.
    """
    context=format_context(documents)

    prompt_template=get_rag_prompt()

    final_prompt=prompt_template.format(
        context=context,
        question=question
    )

    llm=get_llm()

    response=llm.invoke(final_prompt)

    return RAGResponse(
        answer=response.content,
        sources=get_sources(documents)
    )

def ask_question(
    question:str,
    k: int=TOP_K_RESULTS,
    hybrid: bool | None=None,
    persist_directory: str | None=None,
)->RAGResponse:
    """
    Execute complete RAG pipeline.

    Args:
        question:User question
        k: Number of retrieved chunks
        hybrid: BM25 + vector retrieval (default: USE_HYBRID_RETRIEVAL)
        persist_directory: Vector store folder (default: VECTOR_DB_DIRECTORY)

    Returns:
        Generated Answer
    """
    documents=retrieve_documents(
        question,
        k=k,
        hybrid=hybrid,
        persist_directory=persist_directory
    )

    return generate_answer(question, documents)

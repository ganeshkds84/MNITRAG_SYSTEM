from rag.llm import get_llm
from rag.retriever import get_retriever
from rag.prompt_builder import (
    format_context,
    get_rag_prompt
)
from rag.schemas import RAGResponse

def ask_question(
    question:str,
    k: int=3,    
)->RAGResponse:
    """
    Execute complete RAG pipeline.
    
    Args:
        question:User question
        k: Number of retrieved chunks
        
    Returns:
        Generated Answer
    """
    
    retriever=get_retriever(k=k)
    documents=retriever.invoke(question)
    
    context=format_context(documents)
    
    prompt_template=get_rag_prompt()
    
    final_prompt=prompt_template.format(
        context=context,
        question=question
    )
    
    llm=get_llm()
    
    response=llm.invoke(final_prompt)
    
    sources=[]
    
    for doc in documents:
        source_info={
            'source':doc.metadata.get(
                'source',
                'Unknown'
            ),
            'page':doc.metadata.get(
                'page',
                'Unknown'
            ),
            'page_label':doc.metadata.get(
                'page_label',
                'Unknown'
            )
        }
    
        if source_info not in sources:
            sources.append(source_info)
        
    
    return RAGResponse(
        answer=response.content,
        sources=sources
    )
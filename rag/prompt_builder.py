from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

RAG_PROMPT_TEMPLATE="""
You are a helpful AI Assistant

Use only the provided context to answer the question.

If the answer is not present in the context, say:

"I could not find the answer in the provided documents."

Do not make up information.

Context:
{context}

Question:
{question}

Answer:
"""

def format_context(documents: list[Document])->str:
    """
    Convert retrieved documents into a single context string.
    """
    
    return '\n\n'.join(
        doc.page_content
        for doc in documents
    )
    
def get_rag_prompt()-> PromptTemplate:
    """
    Return reusable RAG prompt template.
    """
    
    return PromptTemplate(
        template=RAG_PROMPT_TEMPLATE,
        input_variables=[
            "context",
            "question"
        ]
    )

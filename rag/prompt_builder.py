from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

# Exact sentence returned when the context has no answer.
# app.py hides sources only when the answer equals this sentence.
FALLBACK_ANSWER = "I could not find the answer in the provided documents."

RAG_PROMPT_TEMPLATE = """
You are a helpful AI Assistant for MNIT Jaipur academic and administrative documents.

Each context chunk starts with a header like:
[Source: <file name> | page <page> | category: <category> | year: <year> | OCR: yes/no]

Rules:
1. Use only the provided context to answer the question. Do not make up information.
2. If the answer is not present in the context, reply with exactly this sentence and nothing else:
""" + FALLBACK_ANSWER + """
3. Cite the file name and page for every fact you use, e.g. (FeePG2025-26.pdf, page 3).
4. If sources from different years give different values, prefer the most recent year,
   state which year you are using, and briefly mention the older value and its year.
   Treat "year: unknown" as undated.
5. Chunks marked "OCR: yes" come from scanned pages and may contain recognition errors.
   If such text looks garbled or unclear (e.g. broken numbers, symbols or tables),
   say explicitly that the source is a scanned/OCR page and the value may be inaccurate.

Context:
{context}

Question:
{question}

Answer:
"""


def format_source_header(doc: Document) -> str:
    """
    Build a header describing where a chunk came from, e.g.
    [Source: FeePG2025-26.pdf | page 3 | category: public | year: 2025-26 | OCR: no]
    """
    meta = doc.metadata

    file_name = meta.get("file_name") or meta.get("source", "Unknown")

    page = meta.get("page_label")
    if not page:
        page = meta.get("page", -1) + 1 if "page" in meta else "unknown"

    category = meta.get("category", "unknown")
    year = meta.get("doc_year", "unknown")
    ocr = "yes" if meta.get("ocr") else "no"

    return (
        f"[Source: {file_name} | page {page} | "
        f"category: {category} | year: {year} | OCR: {ocr}]"
    )


def format_context(documents: list[Document])->str:
    """
    Convert retrieved documents into a single context string,
    prefixing each chunk with its source header.
    """

    return '\n\n'.join(
        f"{format_source_header(doc)}\n{doc.page_content}"
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

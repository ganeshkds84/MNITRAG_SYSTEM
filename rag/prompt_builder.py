from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from rag.metadata import page_number, strip_chunk_header

# Exact sentence returned when the context has no answer.
# app.py hides sources only when the answer equals this sentence.
FALLBACK_ANSWER = "I could not find the answer in the provided documents."

RAG_PROMPT_TEMPLATE = """
You are a helpful AI Assistant for MNIT Jaipur academic and administrative documents.

Each context chunk starts with a header like:
[Source: <file name> | page <page> | category: <category> | year: <year> | OCR: yes/no | section: <page title>]
The section (when present) is the page's own title, e.g. which programme and student
type a fee table applies to.

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
6. Never infer, reconstruct or guess what a garbled OCR passage says, and never claim
   that it agrees with (or matches) another source. If a passage is unreadable, say that
   it is unreadable (naming the file and page) and base the answer only on readable text.
   Only say that sources agree when each of them clearly states the same value.
7. When a fee or rule differs by category, programme or student type (e.g. General vs SC/ST,
   full-time vs part-time, regular vs DASA/ICCR or Study in India, income group), do not pick
   one: list each variant found in the context with its value and source. If the question
   names a specific variant, answer that one first, then briefly list the others.
   (Differences between years are handled by rule 4.)

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

    page = page_number(meta)

    category = meta.get("category", "unknown")
    year = meta.get("doc_year", "unknown")
    ocr = "yes" if meta.get("ocr") else "no"
    section = f" | section: {meta['page_title']}" if meta.get("page_title") else ""

    return (
        f"[Source: {file_name} | page {page} | "
        f"category: {category} | year: {year} | OCR: {ocr}{section}]"
    )


def format_context(documents: list[Document])->str:
    """
    Convert retrieved documents into a single context string,
    prefixing each chunk with its source header. The contextual chunk
    header used for embedding (if any) is stripped to avoid duplication.
    """

    return '\n\n'.join(
        f"{format_source_header(doc)}\n{strip_chunk_header(doc)}"
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

from rag.loader import load_pdf
from rag.splitter import split_documents
from rag.vectordb import (
    get_vector_store,
    clear_vector_store,
    )

def ingest_pdf(pdf_path):
    clear_vector_store()
    
    documents=load_pdf(pdf_path)
    chunks=split_documents(documents)
    vector_store=get_vector_store()
    vector_store.add_documents(chunks)
    
    print(f'Successfully ingested {len(chunks)} chunks.')
    
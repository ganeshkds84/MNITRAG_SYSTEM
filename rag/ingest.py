import os

from rag.loader import load_pdf
from rag.splitter import split_documents
from rag.vectordb import (
    get_vector_store,
    clear_vector_store,
    )

def ingest_folder(folder_path: str):
    """
    Recursively ingest all PDFs
    from a folder and its subfolders.
    """
    clear_vector_store()
    
    vector_store=get_vector_store()
    
    total_chunks=0
    total_files=0
    
    for root, _, files in os.walk(folder_path):
        
        for file_name in files:
            
            if not file_name.lower().endswith(".pdf"):
                continue
            
            pdf_path=os.path.join(
                root,
                file_name
            )
            
            print(
                f"\nProcessing: {pdf_path}"
            )
            
            documents=load_pdf(pdf_path)
            
            if not documents:
                print(
                    f"Skipping {file_name}"
                    f"(empty PDF)"
                )
                continue
            
            chunks=split_documents(documents)
            
            if not chunks:
                print(
                    f"Skipping {file_name}"
                    f"(no chunks generated)"
                )
                continue
            
            vector_store.add_documents(
                chunks
            )
            
            total_chunks+=len(chunks)
            total_files+=1
            
            print(
                f"Added {len(chunks)} chunks"
            )
            
    print("\n"+"="*60)
    
    print(
        f"Ingested {total_files} PDFs"
    )
    
    print(
        f"Stored {total_chunks} chunks"
    )
    
    print("="*60)
                
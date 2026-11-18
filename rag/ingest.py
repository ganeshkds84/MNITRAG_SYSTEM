import argparse
import os
import re

from rag.loader import load_pdf
from rag.metadata import enrich_metadata, file_hash
from rag.splitter import split_documents
from rag.vectordb import (
    get_vector_store,
    clear_vector_store,
    )

def ingest_folder(folder_path: str):
    """
    Recursively ingest all PDFs
    from a folder and its subfolders.

    Byte-identical files (same SHA256) are ingested only once.
    """
    clear_vector_store()
    
    vector_store=get_vector_store()
    
    total_chunks=0
    total_files=0
    skipped_files=[]
    seen_hashes={}

    for root, dirs, files in os.walk(folder_path):

        dirs.sort()

        # Process originals before copies like "name (1).pdf"
        files=sorted(
            files,
            key=lambda name: (
                re.search(r"\(\d+\)", name) is not None,
                name
            )
        )

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
            
            content_hash=file_hash(pdf_path)

            if content_hash in seen_hashes:
                original=seen_hashes[content_hash]
                print(
                    f"Skipping {file_name} "
                    f"(duplicate of {original})"
                )
                skipped_files.append(
                    f"{pdf_path} (duplicate of {original})"
                )
                continue

            seen_hashes[content_hash]=pdf_path

            documents=load_pdf(pdf_path)
            
            if not documents:
                print(
                    f"Skipping {file_name} "
                    f"(empty PDF)"
                )
                skipped_files.append(
                    f"{pdf_path} (empty PDF)"
                )
                continue
            
            ocr_pages=sum(
                1 for doc in documents
                if doc.metadata.get("ocr")
            )
            
            print(
                f"Loaded {len(documents)} pages "
                f"({ocr_pages} via OCR)"
            )
            
            documents=enrich_metadata(
                documents,
                pdf_path,
                folder_path
            )

            chunks=split_documents(documents)
            
            if not chunks:
                print(
                    f"Skipping {file_name} "
                    f"(no chunks generated)"
                )
                skipped_files.append(
                    f"{pdf_path} (no chunks generated)"
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
    
    if skipped_files:
        print(
            f"\nSkipped {len(skipped_files)} PDFs:"
        )
        for skipped in skipped_files:
            print(f"  - {skipped}")
    else:
        print("No PDFs were skipped")

    print("="*60)


def main():
    """
    Command-line entry point:
        python -m rag.ingest [--data-dir data/Raw]
    """
    parser=argparse.ArgumentParser(
        description="Rebuild the vector store from a folder of PDFs."
    )
    parser.add_argument(
        "--data-dir",
        default="data/Raw",
        help="Folder containing PDFs (default: data/Raw)"
    )
    args=parser.parse_args()

    if not os.path.isdir(args.data_dir):
        parser.error(f"Folder not found: {args.data_dir}")

    ingest_folder(args.data_dir)


if __name__=="__main__":
    main()
                
import argparse
import os
import re

from config.config import TABLE_ROW_FILES, USE_CHUNK_HEADERS, USE_TABLE_ROWS
from rag.loader import load_pdf
from rag.metadata import add_chunk_headers, enrich_metadata, file_hash
from rag.table_rows import build_table_row_documents
from rag.splitter import split_documents
from rag.vectordb import (
    get_vector_store,
    clear_vector_store,
    )

def ingest_folder(
    folder_path: str,
    use_headers: bool=USE_CHUNK_HEADERS,
    persist_directory: str | None=None,
    use_table_rows: bool=USE_TABLE_ROWS,
):
    """
    Recursively ingest all PDFs
    from a folder and its subfolders.

    Byte-identical files (same SHA256) are ingested only once.

    Args:
        folder_path: Folder containing PDFs
        use_headers: Prefix chunks with a contextual header before embedding
        persist_directory: Vector store folder (default: VECTOR_DB_DIRECTORY)
        use_table_rows: Also add one chunk per fee-table row for TABLE_ROW_FILES
    """
    clear_vector_store(persist_directory)

    vector_store=get_vector_store(persist_directory)

    print(
        f"Chunk headers: {'on' if use_headers else 'off'} | "
        f"table rows: {'on' if use_table_rows else 'off'}"
    )

    total_table_rows=0
    
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

            for chunk in chunks:
                chunk.metadata["chunk_type"]="text"

            # Fee-table rows as extra, self-contained chunks
            if use_table_rows and file_name in TABLE_ROW_FILES:
                rows=build_table_row_documents(pdf_path, documents)
                chunks+=rows
                total_table_rows+=len(rows)
                print(
                    f"Added {len(rows)} table-row chunks"
                )

            if use_headers:
                chunks=add_chunk_headers(chunks)

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
        f"Stored {total_chunks} chunks "
        f"({total_table_rows} of them table rows)"
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
        python -m rag.ingest [--data-dir data/Raw] [--db-dir DIR]
                             [--headers on|off] [--table-rows on|off]
    """
    parser=argparse.ArgumentParser(
        description="Rebuild the vector store from a folder of PDFs."
    )
    parser.add_argument(
        "--data-dir",
        default="data/Raw",
        help="Folder containing PDFs (default: data/Raw)"
    )
    parser.add_argument(
        "--db-dir",
        default=None,
        help="Vector store folder (default: VECTOR_DB_DIRECTORY in config)"
    )
    parser.add_argument(
        "--headers",
        choices=["on","off"],
        default="on" if USE_CHUNK_HEADERS else "off",
        help="Contextual chunk headers (default: USE_CHUNK_HEADERS in config)"
    )
    parser.add_argument(
        "--table-rows",
        choices=["on","off"],
        default="on" if USE_TABLE_ROWS else "off",
        help="Fee-table row chunks (default: USE_TABLE_ROWS in config)"
    )
    args=parser.parse_args()

    if not os.path.isdir(args.data_dir):
        parser.error(f"Folder not found: {args.data_dir}")

    ingest_folder(
        args.data_dir,
        use_headers=args.headers=="on",
        persist_directory=args.db_dir,
        use_table_rows=args.table_rows=="on"
    )


if __name__=="__main__":
    main()
                
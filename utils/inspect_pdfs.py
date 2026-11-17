"""
List every PDF under a folder with its page count and the number of
characters PyPDFLoader extracts, to identify scanned (image-only) PDFs.

Usage:
    python -m utils.inspect_pdfs [--data-dir data/Raw]
"""

import argparse
import os
import sys

from langchain_community.document_loaders import PyPDFLoader


def inspect_folder(folder_path: str):
    """
    Print page count and extracted character count for each PDF.
    """
    rows = []

    for root, _, files in os.walk(folder_path):
        for file_name in sorted(files):
            if not file_name.lower().endswith(".pdf"):
                continue

            pdf_path = os.path.join(root, file_name)

            try:
                pages = PyPDFLoader(pdf_path).load()
                chars = sum(len(p.page_content.strip()) for p in pages)
                rows.append((pdf_path, len(pages), chars))
            except Exception as error:
                rows.append((pdf_path, -1, -1))
                print(f"Error reading {pdf_path}: {error}")

    print(f"{'PAGES':>5}  {'CHARS':>8}  STATUS   FILE")

    for pdf_path, n_pages, chars in rows:
        status = "SCANNED" if chars < 30 * max(n_pages, 1) else "text"
        rel = os.path.relpath(pdf_path, folder_path)
        print(f"{n_pages:>5}  {chars:>8}  {status:<7}  {rel}")

    scanned = sum(1 for _, n, c in rows if c < 30 * max(n, 1))
    print(f"\nTotal PDFs: {len(rows)} | likely scanned: {scanned}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/Raw")
    args = parser.parse_args()

    # Some file names contain non-ASCII characters (e.g. narrow no-break space)
    sys.stdout.reconfigure(encoding="utf-8")

    inspect_folder(args.data_dir)

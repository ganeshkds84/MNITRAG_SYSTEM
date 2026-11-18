import hashlib
import os
import re

UNKNOWN_YEAR = "unknown"

# Academic year such as "2024-25" / "2025-2026" (second part must be next year)
ACADEMIC_YEAR_PATTERN = re.compile(
    r"(?<!\d)((?:19|20)\d{2})-(\d{4}|\d{2})(?!\d)"
)

# Single year such as "2022", "2016" or "2024S" (optional one-letter suffix)
SINGLE_YEAR_PATTERN = re.compile(r"(?<!\d)((?:19|20)\d{2})([A-Za-z]?)(?![A-Za-z\d])")


def parse_doc_year(file_name: str) -> tuple[str, int]:
    """
    Parse the document year from a file name.

    Examples:
        "FeePG2025-26.pdf"          -> ("2025-26", 2025)
        "PG_Manual2024S.pdf"        -> ("2024S", 2024)
        "PG_Manual2022.pdf"         -> ("2022", 2022)
        "Screenshot+2025-09-01.pdf" -> ("2025", 2025)   (a date, not 2025-26)
        "UFM.pdf"                   -> ("unknown", 0)

    Returns:
        (year as written, sortable integer start year; 0 if unknown)
    """
    name = os.path.splitext(file_name)[0]

    for match in ACADEMIC_YEAR_PATTERN.finditer(name):
        start, end = int(match.group(1)), int(match.group(2))

        if end in ((start + 1) % 100, start + 1):
            return match.group(0), start

    match = SINGLE_YEAR_PATTERN.search(name)

    if match:
        return match.group(0), int(match.group(1))

    return UNKNOWN_YEAR, 0


def get_category(pdf_path: str, data_root: str) -> str:
    """
    Return the first subfolder under data_root (faculty / student / public).
    """
    relative = os.path.relpath(os.path.dirname(pdf_path), data_root)
    first_part = relative.split(os.sep)[0]

    return first_part if first_part not in ("", ".") else "unknown"


def file_hash(pdf_path: str) -> str:
    """
    SHA256 of the file contents, used to skip identical files.
    """
    sha256 = hashlib.sha256()

    with open(pdf_path, "rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            sha256.update(block)

    return sha256.hexdigest()


def enrich_metadata(documents, pdf_path: str, data_root: str):
    """
    Add file_name, category, doc_year and doc_year_start to every document.
    All values are str/int so they can be stored in Chroma.
    """
    file_name = os.path.basename(pdf_path)
    category = get_category(pdf_path, data_root)
    doc_year, doc_year_start = parse_doc_year(file_name)

    for doc in documents:
        doc.metadata["file_name"] = file_name
        doc.metadata["category"] = category
        doc.metadata["doc_year"] = doc_year
        doc.metadata["doc_year_start"] = doc_year_start

    return documents

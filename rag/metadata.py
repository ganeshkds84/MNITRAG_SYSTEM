import hashlib
import os
import re
from datetime import datetime

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


# "Dated: 20 April, 2021", "Date-7.12.2020", "Dated:208/2025" (OCR-tolerant:
# any characters on the same line before the year)
DATED_PATTERN = re.compile(
    r"\b(?:dated|date|dt)\b[^\n]{0,25}?(?<!\d)((?:19|20)\d{2})(?!\d)",
    re.IGNORECASE,
)

ANY_YEAR_PATTERN = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")


def parse_year_from_text(text: str, max_year: int) -> tuple[str, int, str]:
    """
    Parse the document year from page text, for files whose name has no year.

    1. The year in a "Dated: ..." line (issue date of an office order)
    2. Otherwise the latest year mentioned in the text (amendments
       usually cite older regulations, so the latest year is the issue year)

    Years after max_year are ignored as OCR noise.

    Returns:
        (year as string, integer year, source: "dated" / "first_page" / "unknown")
    """
    for match in DATED_PATTERN.finditer(text):
        year = int(match.group(1))
        if year <= max_year:
            return str(year), year, "dated"

    years = [
        int(year) for year in ANY_YEAR_PATTERN.findall(text)
        if int(year) <= max_year
    ]

    if years:
        latest = max(years)
        return str(latest), latest, "first_page"

    return UNKNOWN_YEAR, 0, "unknown"


# Tokens for turning a file name into a readable title. Order matters:
# years and known mixed-case terms first, then ALLCAPS runs, then words.
TITLE_TOKEN_PATTERN = re.compile(
    r"(?:19|20)\d{2}(?:-\d{4}|-\d{2})?[A-Z]?(?![a-z])"  # 2024-25, 2024S
    r"|M\.Tech|B\.Tech|B\.Arch|M\.Plan|BTech|MTech|PhD"   # known terms
    r"|[A-Z]+(?=[A-Z][a-z])"                              # CGPA in CGPAConversion
    r"|[A-Z]+(?![a-z])"                                   # PG, UG, UFM
    r"|[A-Z][a-z]+"                                       # Fee, Manual
    r"|[a-z]+"
    r"|\d+(?:st|nd|rd|th)(?![a-z])"                       # 1st, 3rd
    r"|\d+(?:\.\d+)?"
)

TITLE_REPLACEMENTS = {"BTech": "B.Tech", "MTech": "M.Tech", "UGPG": "UG PG"}


def readable_title(file_name: str) -> str:
    """
    Turn a file name into a readable title for chunk headers.

    Examples:
        "FeePG2025-26.pdf"               -> "Fee PG 2025-26"
        "UGRegulationsManual2024.pdf"    -> "UG Regulations Manual 2024"
        "CGPAConversion Formula2014.pdf" -> "CGPA Conversion Formula 2014"
        "...for BTechB.Arch qualified"   -> "... for B.Tech B.Arch qualified"
    """
    name = os.path.splitext(file_name)[0]
    tokens = TITLE_TOKEN_PATTERN.findall(name)

    return " ".join(TITLE_REPLACEMENTS.get(token, token) for token in tokens)


def page_number(metadata: dict):
    """
    Human page number: page_label if present, else page + 1.
    """
    page = metadata.get("page_label")

    if page:
        return page

    return metadata["page"] + 1 if "page" in metadata else "unknown"


def build_chunk_header(metadata: dict) -> str:
    """
    Short header prefixed to a chunk before embedding / BM25 indexing, e.g.
    "Document: Fee PG 2025-26 | Category: public | Year: 2025-26 | Page: 1"
    """
    return (
        f"Document: {readable_title(metadata.get('file_name', ''))} | "
        f"Category: {metadata.get('category', 'unknown')} | "
        f"Year: {metadata.get('doc_year', 'unknown')} | "
        f"Page: {page_number(metadata)}"
    )


def add_chunk_headers(chunks):
    """
    Prefix each chunk's text with its header and remember the header in
    metadata["chunk_header"] so it can be stripped again for the prompt.
    """
    for chunk in chunks:
        header = build_chunk_header(chunk.metadata)
        chunk.metadata["chunk_header"] = header
        chunk.page_content = f"{header}\n{chunk.page_content}"

    return chunks


def strip_chunk_header(doc) -> str:
    """
    Return the chunk text without the header added by add_chunk_headers().
    """
    header = doc.metadata.get("chunk_header")

    if header and doc.page_content.startswith(header):
        return doc.page_content[len(header):].lstrip("\n")

    return doc.page_content


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
    Add file_name, category, doc_year, doc_year_start and doc_year_source
    to every document. The year comes from the file name, or from the
    first page text if the file name has none.
    All values are str/int so they can be stored in Chroma.
    """
    file_name = os.path.basename(pdf_path)
    category = get_category(pdf_path, data_root)
    doc_year, doc_year_start = parse_doc_year(file_name)
    doc_year_source = "file_name"

    if doc_year == UNKNOWN_YEAR and documents:
        doc_year, doc_year_start, doc_year_source = parse_year_from_text(
            documents[0].page_content,
            max_year=datetime.now().year + 1,
        )

    for doc in documents:
        doc.metadata["file_name"] = file_name
        doc.metadata["category"] = category
        doc.metadata["doc_year"] = doc_year
        doc.metadata["doc_year_start"] = doc_year_start
        doc.metadata["doc_year_source"] = doc_year_source

    return documents

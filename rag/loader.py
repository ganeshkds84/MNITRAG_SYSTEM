import pytesseract
from langchain_community.document_loaders import PyPDFLoader
from pdf2image import convert_from_path

from config.config import (
    OCR_DPI,
    OCR_LANGUAGE,
    OCR_MIN_CHARS,
    POPPLER_PATH,
    TESSERACT_CMD,
)

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def ocr_page(pdf_path: str, page_number: int) -> str:
    """
    Render a single PDF page to an image and OCR it.

    Args:
        pdf_path: Path to the PDF
        page_number: 1-based page number

    Returns:
        OCR text of the page
    """
    images = convert_from_path(
        pdf_path,
        dpi=OCR_DPI,
        first_page=page_number,
        last_page=page_number,
        poppler_path=POPPLER_PATH,
    )

    return "\n".join(
        pytesseract.image_to_string(image, lang=OCR_LANGUAGE)
        for image in images
    )


def load_pdf(pdf_path):
    """
    Load a PDF page by page. Pages with too little extractable text
    (scanned images) are OCR'd. Sets metadata["ocr"] on every page and
    drops pages that are still empty.
    """
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    loaded = []

    for doc in documents:
        doc.metadata["ocr"] = False

        if len(doc.page_content.strip()) < OCR_MIN_CHARS:
            page_number = doc.metadata.get("page", 0) + 1

            try:
                doc.page_content = ocr_page(pdf_path, page_number)
                doc.metadata["ocr"] = True
            except Exception as error:
                print(
                    f"Warning: OCR failed for {pdf_path} "
                    f"page {page_number}: {error}"
                )

        if doc.page_content.strip():
            loaded.append(doc)

    return loaded

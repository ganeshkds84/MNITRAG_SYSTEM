import os

from dotenv import load_dotenv

load_dotenv()


# ===========================
# Groq Configuration
# ===========================

LLM_MODEL = "openai/gpt-oss-120b"

LLM_TEMPERATURE = 0


# ===========================
# HuggingFace Embedding Model
# ===========================

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ===========================
# ChromaDB Configuration
# ===========================

VECTOR_DB_DIRECTORY = "vector_store"


# ===========================
# Text Splitting Configuration
# ===========================

CHUNK_SIZE = 1000

CHUNK_OVERLAP = 200


# ===========================
# Retrieval Configuration
# ===========================

TOP_K_RESULTS = 6

# Hybrid retrieval: BM25 (keyword) + vector (semantic), fused by EnsembleRetriever
USE_HYBRID_RETRIEVAL = True

BM25_WEIGHT = 0.5

VECTOR_WEIGHT = 0.5


# ===========================
# OCR Configuration (scanned PDFs)
# ===========================

# Pages with fewer extracted characters than this are OCR'd
OCR_MIN_CHARS = 30

OCR_LANGUAGE = "eng"

OCR_DPI = 300

# Read from .env / environment. Leave unset (None) if tesseract and
# Poppler's pdftoppm are already on PATH (typical on Linux/macOS).
TESSERACT_CMD = os.getenv("TESSERACT_CMD") or None

POPPLER_PATH = os.getenv("POPPLER_PATH") or None
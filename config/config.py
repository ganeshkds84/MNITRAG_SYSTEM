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

TOP_K_RESULTS = 4
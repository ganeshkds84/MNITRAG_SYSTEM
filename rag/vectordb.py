from langchain_chroma import Chroma
import shutil
import os

from config.config import VECTOR_DB_DIRECTORY
from rag.embedding import get_embedding_model

def get_vector_store():
    
    embedding_model=get_embedding_model()
    vector_store=Chroma(
        persist_directory=VECTOR_DB_DIRECTORY,
        embedding_function=embedding_model
    )
    
    return vector_store

def clear_vector_store():
    
    if os.path.exists(VECTOR_DB_DIRECTORY):
        shutil.rmtree(VECTOR_DB_DIRECTORY)
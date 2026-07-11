from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.config import CHUNK_OVERLAP,CHUNK_SIZE

def split_documents(documents):
    
    text_splitter=RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    chunks=text_splitter.split_documents(documents)
    
    return chunks

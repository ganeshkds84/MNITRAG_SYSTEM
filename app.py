import streamlit as st 
import os

from rag.pipeline import ask_question
from rag.vectordb import get_vector_store_stats

st.set_page_config(
    page_title="MNIT ASSISTANT",
    page_icon="📚",
    layout="wide"
)

stats=get_vector_store_stats()

with st.sidebar:
    
    st.header("MNITRAG")
    
    st.markdown(
        f"""
        **LLM:** Groq
        
        **Embeddings:** all-MiniLM-L6-v2
        
        **Vector DB:** ChromaDB
        
        **Documents:** {stats["sources"]} PDFs
        
        **Chunks:** {stats["chunks"]}
        """
    )
    
    st.divider()
    
    st.markdown(
        "Retrieval-Augmented Generation "
        "system for MNIT documents."
    )

st.title("📚 MNIT ASSISTANT")

st.markdown(
    "AI-powered assistant for MNIT academic and administrative documents."
)

if stats["chunks"]==0:
    st.error(
        "The vector store is missing or empty. "
        "Build it first by running:\n\n"
        "`python -m rag.ingest`\n\n"
        "then refresh this page."
    )
    st.stop()

question=st.text_input(
    "Enter your question"
)

if st.button("Submit"):
    
    if not question.strip():
        st.warning(
            "Please enter a question."
        )
        
    else:
        
        with st.spinner(
            "Searching documents..."
        ):
            response=ask_question(
                question
            )
            
            answer_text=response.answer.lower()
            
            show_sources=True
            
            if (
                "could not find" in answer_text
                or "not found" in answer_text 
                or "not available" in answer_text
            ):
                show_sources=False
            
        st.subheader("Answer")
        
        st.write(
            response.answer
        )
        
        if show_sources and response.sources:
            st.subheader("Sources")
            
            for source in response.sources:
                
                source_name=os.path.basename( 
                    source.get("source","Unknown")
                )
                
                page=source.get(
                    "page_label",
                    source.get(
                        "page",
                        "Unknown"
                    )
                )
                
                st.write(
                    f"📑 {source_name} (Page {page})"
                )
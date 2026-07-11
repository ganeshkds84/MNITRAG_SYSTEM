import os

from dotenv import  load_dotenv
from langchain_groq import ChatGroq

from config.config import LLM_MODEL,LLM_TEMPERATURE

load_dotenv()

def get_llm():
    api_key=os.getenv('GROQ_API_KEY')
    
    if not api_key:
        raise ValueError('GROQ_API_KEY not found. Please check your .env file.')
    
    llm=ChatGroq(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        api_key=api_key
    )
    
    return llm
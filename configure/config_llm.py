from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from Model.provider import ModelProvider
from typing import Union
from config.settings import GROQ_API_KEY

def configure_llm(provider: str) -> Union[ChatOllama, ChatGroq]:
    """Configure LLM based on selected provider."""
    if provider == ModelProvider.OLLAMA:
        return ChatOllama(
            model="llama3.2:3b-instruct-q8_0",
            base_url="http://localhost:11434",
            temperature=0.5,
            num_gpu=1,
            num_thread=8
        )
    else:
        return ChatGroq(
            model="llama-3.3-70b-specdec",
            temperature=0.5,
            groq_api_key=GROQ_API_KEY
        )
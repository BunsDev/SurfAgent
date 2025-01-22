from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from Model.provider import ModelProvider
from typing import Union
from config.settings import GROQ_API_KEY

def configure_vision_model(provider: str) -> Union[ChatOllama, ChatGroq]:
    """Configure vision model based on selected provider."""
    if provider == ModelProvider.OLLAMA:
        return ChatOllama(
            model="llama3.2-vision:11b",
            base_url="http://localhost:11434",
            temperature=0.5,
            num_gpu=1,
            num_thread=8,
            madvise=True,
            f16=True
        )
    else:
        return ChatGroq(
            model="llama-3.2-90b-vision-preview",
            temperature=0.5,
            groq_api_key=GROQ_API_KEY
        )
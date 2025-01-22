from Model.provider import ModelProvider
from langchain.prompts import PromptTemplate
from configure.config_llm import configure_llm
from config.log import logger
import sys

def configure_llama():
    """Configure model and prompt based on user's choice."""
    provider = ModelProvider.get_provider_choice()
        logger.error(f"Failed to initialize {provider} models")
        sys.exit(1)
    llm = configure_llm(provider)
    prompt = PromptTemplate(
        template="""You are an assistant for research tasks. Use the following documents to provide a comprehensive and concise report on the topic. Ensure the report is self-contained with all necessary information.

        Topic: {topic}
        Documents: {documents}
        Report: """,
        input_variables=["topic", "documents"],
    )
    return llm, prompt, provider
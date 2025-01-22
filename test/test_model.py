from config.log import logger
from Model.provider import ModelProvider
from config.settings import GROQ_API_KEY
import requests
from test.ollama import test_ollama

def test_model_provider(provider: str) -> bool:
    """Test if the selected model provider is accessible."""
    try:
        if provider == ModelProvider.OLLAMA:
            return test_ollama()
        else:
            if not GROQ_API_KEY:
                logger.error("GROQ_API_KEY not set.")
                return False
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            response = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
            response.raise_for_status()
            logger.info("✅ Groq API is accessible")
            return True
    except Exception as e:
        logger.error(f"❌ {provider.capitalize()} test failed: {str(e)}")
        return False
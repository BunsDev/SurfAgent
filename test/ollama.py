from config.log import logger
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, AIMessage

def test_ollama() -> bool:
    """Test if Ollama is running and accessible."""
    try:
        test_llm = ChatOllama(
            model="llama3.2:3b-instruct-q8_0",
            base_url="http://localhost:11434",
            temperature=0,
            num_gpu=1,
            num_thread=8
        )
        resp = test_llm([HumanMessage(content="Hello")])
        if isinstance(resp, AIMessage) and len(resp.content) > 0:
            logger.info("✅ Ollama is accessible")
            return True
        else:
            logger.error("❌ Ollama did not return a valid response")
            return False
    except Exception as e:
        logger.error(f"❌ Ollama test failed: {str(e)}")
        return False
from Model.invokemodel import invoke_model
from config.log import logger
import re

def generate_vision_query(llm, original_query: str) -> str:
    """Generate a focused vision query based on the original research question."""
    prompt = f"""You are a tool assisting in generating natural and concise vision model queries.
    Your task is to transform research questions into specific and actionable prompts that guide the model in analyzing webpage screenshots.
    The queries should:
    - Start with "Describe the image in detail, focusing on".
    - Be natural, concise, and no longer than 15 words.
    - Highlight the most relevant information to answer the research question.
    - Avoid mechanical or vague phrases like "extract X from the image."
    
    Examples:
    Research question: What is the current Tesla stock price?
    Vision query: Describe the image in detail, focusing on the specific Tesla stock price.

    Research question: What are the iPhone 15 specs?
    Vision query: Describe the image in detail, focusing on the iPhone 15 specifications and features.

    Research question: How much does the latest MacBook Pro cost?
    Vision query: Describe the image in detail, focusing on the price of the latest MacBook Pro.

    Research question: {original_query}

    Vision query:"""
    
    try:
        response = invoke_model(llm, prompt)
        vision_query = response.content.strip()
        
        # Clean up and standardize the query
        vision_query = vision_query.replace('"', '').replace("'", '')
        if not vision_query.lower().startswith("describe the image"):
            vision_query = f"Describe the image in detail, focusing on {vision_query}"
        
        # Remove mechanical phrases
        vision_query = vision_query.replace("extract from the image", "")
        vision_query = vision_query.replace("from the image", "")
        vision_query = re.sub(r'\s+', ' ', vision_query).strip()
        
        # Ensure it ends properly
        if vision_query.endswith("focusing on"):
            vision_query = vision_query[:-11].strip()
        
        return vision_query
    except Exception as e:
        logger.error(f"Error generating vision query: {str(e)}")
        return "Describe the image in detail, focusing on the main content and key information."

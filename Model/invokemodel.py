from langchain.schema import HumanMessage, AIMessage

def invoke_model(llm, prompt: str) -> AIMessage:
    """Helper to invoke LLM with a single prompt."""
    response = llm([HumanMessage(content=prompt)])
    return response
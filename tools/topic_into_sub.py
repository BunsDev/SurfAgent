from Model.invokemodel import invoke_model

def decompose_topic_into_subtopics(llm, topic):
    decomposition_prompt = f"""You are a research assistant.
You will be given a research topic. If the topic is broad or complex, break it down into a list of more specific subtopics or sub-questions that would help in researching it thoroughly.
If the topic is simple or already focused, just return it as is.
Format your response as a simple list with one subtopic per line.

Topic: {topic}

Subtopics:"""
    response = invoke_model(llm, decomposition_prompt)
    response_text = response.content
    subtopics = [line.strip("- ").strip() for line in response_text.split("\n") if line.strip()]
    subtopics = [s for s in subtopics if s and not s.lower().startswith(("subtopic", "topic"))]
    return subtopics if subtopics else [topic]
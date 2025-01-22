from langchain_community.vectorstores import SKLearnVectorStore
from langchain_ollama import OllamaEmbeddings

def create_vectorstore(docs_splits):
    embeddings = OllamaEmbeddings(
        model="all-minilm",
        base_url="http://localhost:11434/v1"
    )
    vectorstore = SKLearnVectorStore.from_documents(
        documents=docs_splits,
        embedding=embeddings
    )
    return vectorstore.as_retriever(k=4)
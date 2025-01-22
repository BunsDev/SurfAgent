class ModelProvider:
    OLLAMA = "ollama"
    GROQ = "groq"

    @staticmethod
    def get_provider_choice() -> str:
        return ModelProvider.GROQ
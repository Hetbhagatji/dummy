# app/llm_models/ollama_llm.py
from .base_llm import BaseLLM
from ollama import chat

class OllamaLLM(BaseLLM):
    def __init__(self, model_name: str = "qwen2:0.5b"):
        self.model_name = model_name

    def parse(self, prompt: str) -> str:
        """
        Sends prompt to local Ollama model and expects pure JSON response.
        """

        response = chat(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a resume parser that outputs only JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]

# app/llm_models/factory.py
from app.llm_models.grok_llm import GroqLLM
from app.llm_models.ollama_lllm import OllamaLLM

def get_llm(model_name: str):
    if model_name.lower() == "grokllm":
        return GroqLLM()
    elif model_name.lower() == "ollamallm":
        return OllamaLLM()
    else:
        raise ValueError(f"Unknown LLM model: {model_name}")

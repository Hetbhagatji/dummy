from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

import yaml
from pathlib import Path
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "embedding_model_config.yml"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

config = load_config()

MODEL_NAME = config["embedding_model"]

class ResumeJobEmbedder:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts)
    
    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

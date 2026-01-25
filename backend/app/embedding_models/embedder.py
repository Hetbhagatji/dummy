from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class ResumeJobEmbedder:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts)
    
    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

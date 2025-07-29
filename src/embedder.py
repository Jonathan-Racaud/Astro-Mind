from abc import ABC, abstractmethod

from sentence_transformers import SentenceTransformer

class Embedder(ABC):
    def __init__(self):
        return
    
    @abstractmethod
    def embed_text(self, text: str):
        return

    @abstractmethod
    def embed_document(self, document: list[str]):
        return

class BAAIEmbedder(Embedder):
    def __init__(self):
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    def embed_text(self, text: str):
        return self.model.encode([text], normalize_embedding=True).tolist()[0]
    
    def embed_document(self, document: list[str]):
        return self.model.encode(document, normalize_embeddings=True).tolist()
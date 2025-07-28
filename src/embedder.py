from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self):
        return
    
    def embed_text(self, text):
        return

class BAAIEmbedder(Embedder):
    def __init__(self):
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    def embed_text(self, text):
        return model.encode([text], normalize_embedding=True).toList[0]
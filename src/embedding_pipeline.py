from abc import ABC, abstractmethod

from .vdb import VectorDB

class EmbeddingPipeline(ABC):
    SUCCESS=True
    FAILURE=False

    def __init__(self, vdb: VectorDB):
        self.vdb = vdb
        self.name = ""
        
    @abstractmethod
    def start(self):
        pass
from abc import ABC, abstractmethod

from typing import List

from .chunking import ContentChunk
from .embedder import Embedder

class VectorDB(ABC):
    def __init__(self, embedder: Embedder):
        self.embedder = embedder

    @abstractmethod
    def init_collection(collection_name: str):
        pass

    @abstractmethod
    def add(chunks: List[ContentChunk], collection_name: str):
        pass

    @abstractmethod
    def search(query: str, collection_name: str):
        pass

    # def load(self, force=False):
    #     self.load_ships_data(force)

    # @abstractmethod
    # def load_ships_data(self, force=False):
    #     return

    # def get_context(self, question: str, additional_data) -> str:
    #     return self.get_context_for_ships(question, additional_data)

    # @abstractmethod
    # def get_context_for_ships(self, question: str, additional_data) -> str:
    #     return ""
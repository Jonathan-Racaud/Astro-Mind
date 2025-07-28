from abc import ABC, abstractmethod

class EliteVectorDB(ABC):
    def __init__(self):
        return

    def load(self, force=False):
        self.load_ships_data(force)

    @abstractmethod
    def load_ships_data(force=False):
        return

    def get_context(self, question: str) -> str:
        return self.get_context_for_ships(question)

    @abstractmethod
    def get_context_for_ships(self, question: str) -> str:
        return ""
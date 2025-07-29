from abc import ABC, abstractmethod

class VectorDB(ABC):
    def __init__(self):
        return

    def load(self, force=False):
        self.load_ships_data(force)

    @abstractmethod
    def load_ships_data(self, force=False):
        return

    def get_context(self, question: str, additional_data) -> str:
        return self.get_context_for_ships(question, additional_data)

    @abstractmethod
    def get_context_for_ships(self, question: str, additional_data) -> str:
        return ""
class EliteVectorDB:
    def __init__(self):
        return

    def load(self, force=False):
        load_ships_data(self, force)

    def load_ships_data(self, force=False):
        return

    def get_context(self, question: str) -> str:
        return get_context_for_ships(self, question)

    def get_context_for_ships(self, question: str) -> str:
        return ""
import re

from abc import ABC, abstractmethod

class LLM(ABC):
    def __init__(self, provider: str, api_key: str, model: str, url=None):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.url = url
        self.system_prompt = None
        self.user_prompt = None
    
    @abstractmethod
    def ask(self, context: str, query) -> str:
        return
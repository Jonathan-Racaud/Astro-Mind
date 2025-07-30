from abc import ABC, abstractmethod
from bs4 import BeautifulSoup, Tag
from typing import List

from .chunking import ContentChunk

class BaseHTMLProcessor(ABC):
    ENTITY_TYPE = "generic"
    
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, "html.parser")
        self.entity_name = self._extract_entity_name()
    
    @abstractmethod
    def _extract_entity_name(self) -> str:
        raise NotImplementedError("Subclasses must implement entity name extraction")
    
    @abstractmethod
    def _normalize_section(self, header: str) -> str:
        raise NotImplementedError("Subclasses must implement section normalization")
        
    def extract_chunks(self) -> List[ContentChunk]:
        chunks = []
        current_chunk = None
        
        for element in self.soup.find_all(['h2', 'h3', 'p']):
            if isinstance(element, Tag) and element.name == 'h2':
                section_type = self._normalize_section(element.get_text())
                current_chunk = ContentChunk(
                    entity_type=self.ENTITY_TYPE,
                    entity_name=self.entity_name,
                    section_type=section_type,
                    headers=[element.get_text().strip()],
                    raw_text="",
                    source=""
                )
                chunks.append(current_chunk)
            elif current_chunk and element.name == 'h3':
                current_chunk.headers.append(element.get_text().strip())
            elif current_chunk and element.name == 'p':
                current_chunk.raw_text += element.get_text() + "\n"
                current_chunk.source += str(element)
        
        return chunks

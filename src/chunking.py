from dataclasses import dataclass
from typing import List, Dict, Optional, Any

@dataclass
class ContentChunk:
    entity_type: str
    entity_name: str
    section_type: str
    headers: List[str]
    raw_text: str
    source: str
    infobox: Optional[Dict[str, Any]] = None

class ChunkStrategy:
    MAX_CHUNK_SIZE = 1500
    MIN_CHUNK_SIZE = 300

    @classmethod
    def split_chunks(cls, chunks: List[ContentChunk]) -> List[ContentChunk]:
        optimized = []
        for chunk in chunks:
            if len(chunk.raw_text) <= cls.MAX_CHUNK_SIZE:
                optimized.append(chunk)
                continue
                
            sentences = chunk.raw_text.split('. ')
            current_text = []
            for sentence in sentences:
                if sum(len(t) for t in current_text) + len(sentence) > cls.MAX_CHUNK_SIZE:
                    optimized.append(ContentChunk(
                        entity_type=chunk.entity_type,
                        entity_name=chunk.entity_name,
                        section_type=chunk.section_type,
                        headers=chunk.headers,
                        raw_text='. '.join(current_text),
                        source=chunk.source,
                        infobox=chunk.infobox
                    ))
                    current_text = []
                current_text.append(sentence)
            if current_text:
                optimized.append(ContentChunk(
                    entity_type=chunk.entity_type,
                    entity_name=chunk.entity_name,
                    section_type=chunk.section_type,
                    headers=chunk.headers,
                    raw_text='. '.join(current_text),
                    source=chunk.source,
                    infobox=chunk.infobox
                ))
        return optimized

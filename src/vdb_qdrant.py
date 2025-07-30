import uuid

from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from .chunking import ContentChunk
from .embedder import Embedder
from .vdb import VectorDB

class QdrantVectorDB(VectorDB):
    def __init__(self, embedder: Embedder, db_path: str):
        super().__init__(embedder)
        
        self.client = QdrantClient(path=db_path)
    
    def close(self):
        # QdrantClient doesn't have an explicit close method in local mode
        # but we can set the client to None to release references
        self.client = None

    def init_collection(self, collection_name: str):
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=self.embedder.model.get_sentence_embedding_dimension(),
                distance=Distance.COSINE
            )
        )

    def add(self, chunks: List[ContentChunk], collection_name: str):
        points = []
        for chunk in chunks:
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=self.embedder.embed_text(chunk.raw_text),
                payload={
                    "entity_type": chunk.entity_type,
                    "entity_name": chunk.entity_name,
                    "section_type": chunk.section_type,
                    "headers": chunk.headers,
                    "infobox": chunk.infobox,
                    "html_snippet": chunk.source
                }
            ))
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
    
    def search(self, query, collection_name):
        query_vector = self.embedder.embed_text(query)

        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            with_payload=True
        )
    
        return [hit.payload["html_snippet"] for hit in search_result]

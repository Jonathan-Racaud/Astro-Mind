import os
import re

from thefuzz import fuzz, process

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.models import SearchParams

from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from typing import List, Optional
import uuid

from src.vdb import VectorDB
from src.embedder import Embedder
from src.constants import *
from src.utilities import is_dir_empty

class QdrantVectorDB(VectorDB):
    def __init__(self, embedder: Embedder):
        self.client = QdrantClient(path="./astro-mind-qdrant.db")  # Local embedded Qdrant instance
        self.ship_collection_name = "ships"
        self.embedder = embedder

    def _ensure_collection(self):
        if self.ship_collection_name not in self.client.get_collections().collections:
            self.client.recreate_collection(
                collection_name=self.ship_collection_name,
                vectors_config=VectorParams(
                    size=len(self.embedder.embed_text("test")),
                    distance=Distance.COSINE
                )
            )

    def load_ships_data(self, force=False):
        if force:
            self._ensure_collection()
        
        if self.client.collection_exists(self.ship_collection_name) and not force:
            print("[INFO]: Ships vector DB exists. Skipping ship loading process")
            return
        else:
            self._ensure_collection()

        transformed_data_dir = f"{SHIPS_DATA_DIR}/transformed_data"
        
        if is_dir_empty(f"{transformed_data_dir}"):
            print("[ERROR]: No available extracted ship data to process")
            return
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        for filename in os.listdir(transformed_data_dir):
            file_path = os.path.join(transformed_data_dir, filename)

            # Skip directories or non-JSON files
            if not os.path.isfile(file_path) or not filename.lower().endswith((".json", ".jsonl")):
                continue

            print(f"Embedding: {filename}")
            loader = JSONLoader(
                file_path=file_path,
                jq_schema=".",
                content_key="text",
                json_lines=True,
                metadata_func=self._metadata_extractor
            )

            docs = loader.load()
            chunks = text_splitter.split_documents(docs)

            documents = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]

            self._add_documents(documents, metadatas)

    def _add_documents(self, documents: List[str], metadatas: List[dict] = None):
        embeddings = self.embedder.embed_document(documents)

        points = []
        for doc, metadata, vector in zip(documents, metadatas, embeddings):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=metadata
            ))
        
        upsert_result = self.client.upsert(collection_name=self.ship_collection_name, points=points)

        print(f"=> Result of embedding: {upsert_result}")

    def get_context_for_ships(self, question: str, additional_data) -> List[str]:
        query_vector = self.embedder.embed_text(question)

        # ship_names = self.get_known_ship_names()
        # matched_ship = self.detect_entity_from_query(question, ship_names)

        entity_filter = None
        if additional_data != None:
            entity_filter = Filter(
                should=[
                    FieldCondition(
                        key="entity_name",
                        match=MatchValue(value=additional_data)
                    )
                ]
            )

        search_result = self.client.search(
            collection_name=self.ship_collection_name,
            query_vector=query_vector,
            with_payload=True,
            query_filter=entity_filter
        )

        return [hit.payload["document"] for hit in search_result]

    def _metadata_extractor(self, record: dict, metadata: dict) -> dict:
        # 'record' is the full JSON object for a single line (or the result of the jq_schema)
        # 'metadata' contains default metadata like 'source' and 'seq_num'

        # Add your custom metadata fields
        if 'metadata' in record and isinstance(record['metadata'], dict):
            metadata['entity_name'] = record['metadata'].get('entity_name')
            metadata['document_type'] = record['metadata'].get('document_type')
            metadata['chunk_type'] = record['metadata'].get('chunk_type')
            metadata['document'] = record['text']
        return metadata

    def inspect(self):
        response = self.client.scroll(
            collection_name=self.ship_collection_name,
            limit=100,  # page size
            with_payload=True
        )

        for point in response[0]:
            print(point.id, point.payload)
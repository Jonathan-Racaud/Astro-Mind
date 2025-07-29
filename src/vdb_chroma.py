import chromadb
import os

from tqdm import tqdm

from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.vdb import VectorDB
from src.embedder import Embedder
from src.constants import *
from src.utilities import is_dir_empty

class ChromaVectorDB(VectorDB):
    def __init__(self, embedder: Embedder):
        super().__init__()

        self.embedder = embedder

        self.client = chromadb.PersistentClient()
        self.ship_collection_name = "ships"

    def load_ships_data(self, force=False):
        if force:
            self.client.delete_collection(self.ship_collection_name)

        try:
            self.client.get_collection(self.ship_collection_name)
            
            print("[INFO]: Ships data already in vector db. Skipping ships data loading process.")

            return
        except ValueError as e:
            collection = self.client.get_or_create_collection(self.ship_collection_name)

        transformed_data_dir = f"{SHIPS_DATA_DIR}/transformed_data"
        
        if is_dir_empty(f"{transformed_data_dir}"):
            print("[ERROR]: No available extracted ship data to process")
            return
        
        print("[INFO]: Started ship data loading process.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        for filename in os.listdir(transformed_data_dir):
            file_path = os.path.join(transformed_data_dir, filename)

            # Skip directories or non-JSON files
            if not os.path.isfile(file_path) or not filename.lower().endswith((".json", ".jsonl")):
                continue
            
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
            ids = [f"{filename}-{i}" for i in range(len(chunks))]

            embeddings = self.embedder.embed_document(documents)
            
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

        print("[INFO]: Finished ship data loading process.")

    def get_context_for_ships(self, question):
        collection = self.client.get_collection(self.ship_collection_name)
        
        embeddings = self.embedder.embed_text(question)

        results = collection.query(
            query_embeddings=embeddings,
            n_results=5,
            include=["documents", "metadatas", "distances"]
        )
        
        return results["documents"][0]

    def _metadata_extractor(self, record: dict, metadata: dict) -> dict:
        # 'record' is the full JSON object for a single line (or the result of the jq_schema)
        # 'metadata' contains default metadata like 'source' and 'seq_num'

        # Add your custom metadata fields
        if 'metadata' in record and isinstance(record['metadata'], dict):
            metadata['entity_name'] = record['metadata'].get('entity_name')
            metadata['document_type'] = record['metadata'].get('document_type')
            metadata['chunk_type'] = record['metadata'].get('chunk_type')
        return metadata

import chromadb
import os

from tqdm import tqdm

from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.vdb_elite import EliteVDB
from src.constants import *
from src.utilities import is_dir_empty

class ChromaVectorDB(EliteVDB):
    def __init__(self, embedder):
        super().__init__()

        self.embedder = embedder

        self.client = chromadb.PersistentClient()
        self.ship_collection_name = "ships"

    def load_ships_data(self, force=False):
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

            text_lines = [chunk.page_content for chunk in chunks]

            embeddings = []
            ids = []
            for i, line in enumerate(tqdm(text_lines)):
                embeddings.append(self.embedder.embed_text(line))
            
            collection.add(
                embeddings=embeddings,
                documents=text_lines,
                ids=ids
            )

        print("[INFO]: Finished ship data loading process.")

    def get_context_for_ships(self, question):
        collection = self.get_collection(self.ship_collection_name)
        
        embeddings = self.embedder.embed_text(question)

        results = collection.query(
            query_embeddings=embeddings,
            n_results=5
        )
        
        return results

    def _metadata_extractor(self, record: dict, metadata: dict) -> dict:
        # 'record' is the full JSON object for a single line (or the result of the jq_schema)
        # 'metadata' contains default metadata like 'source' and 'seq_num'

        # Add your custom metadata fields
        if 'metadata' in record and isinstance(record['metadata'], dict):
            metadata['entity_name'] = record['metadata'].get('entity_name')
            metadata['document_type'] = record['metadata'].get('document_type')
            metadata['chunk_type'] = record['metadata'].get('chunk_type')
        return metadata

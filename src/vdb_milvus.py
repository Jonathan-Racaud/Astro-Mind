import os

from pymilvus import MilvusClient
from tqdm import tqdm

from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.vdb import VectorDB
from src.constants import *
from src.utilities import is_dir_empty

class MilvusVDB(VectorDB):
    def __init__(self, uri, embedder):
        super().__init__()

        self.embedder = embedder

        self.client = MilvusClient(uri=uri)
        self.collection_name = "ships"

    def load_ships_data(self, force=False):
        milvus_has_collection = self.client.has_collection(self.collection_name)

        if milvus_has_collection and not force:
            print("[INFO]: Vector database already created. Skipping ship data loading process.")
            return
        elif milvus_has_collection and force:
            self.client.drop_collection(self.collection_name)

        transformed_data_dir = f"{SHIPS_DATA_DIR}/transformed_data"
        
        if is_dir_empty(f"{transformed_data_dir}"):
            print("[ERROR]: No available extracted ship data to process")
            return
        
        print("[INFO]: Started ship data loading process.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        self.client.create_collection(
            collection_name=self.collection_name,
            dimension=384, # test value for now, need to understand what this value should be.
            metric_type="IP",
            consistency_level="Strong"
        )

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

            data = []
            for i, line in enumerate(tqdm(text_lines)):
                data.append({"id": i, "vector": self.embedder.embed_text(line), "text": line})
            
            self.client.insert(
                collection_name=self.collection_name,
                data=data
            )

    def get_context_for_ships(self, question):
        db_search = self.client.search(
            collection_name=self.collection_name,
            data=[self.embedder.embed_text(question)],
            limit=3,
            search_params={"metric_type": "IP", "params": {}},
            output_fields=["text"]
        )

        retrieved_db_search = [(res["entity"]["text"], res["distance"]) for res in db_search[0]]

        context = "\n".join([db_res[0] for db_res in retrieved_db_search])

        return context
    
    def _metadata_extractor(self, record: dict, metadata: dict) -> dict:
        # 'record' is the full JSON object for a single line (or the result of the jq_schema)
        # 'metadata' contains default metadata like 'source' and 'seq_num'

        # Add your custom metadata fields
        if 'metadata' in record and isinstance(record['metadata'], dict):
            metadata['entity_name'] = record['metadata'].get('entity_name')
            metadata['document_type'] = record['metadata'].get('document_type')
            metadata['chunk_type'] = record['metadata'].get('chunk_type')
        return metadata
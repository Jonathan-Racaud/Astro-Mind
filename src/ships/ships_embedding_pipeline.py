import os

from .ships_html_processor import ShipHTMLProcessor

from ..chunking import ChunkStrategy
from ..constants import SHIPS_DATA_DIR, SHIPS_COLLECTION_NAME, RAW_DATA_FOLDER_NAME
from ..embedding_pipeline import EmbeddingPipeline
from ..vdb import VectorDB

class ShipsEmbeddingPipeline(EmbeddingPipeline):
    def __init__(self, vdb: VectorDB):
        super().__init__(vdb)

        self.name = "Ships Embedding Pipeline"

        self.dataset_dir = f"{SHIPS_DATA_DIR}/{RAW_DATA_FOLDER_NAME}"

    def start(self):
        try:
            self.vdb.init_collection(SHIPS_COLLECTION_NAME)
        except Exception as e:
            print(f"[ERROR]: Failed to initialize vector DB collection {SHIPS_COLLECTION_NAME}: {e}")
            return EmbeddingPipeline.FAILURE

        for filename in os.listdir(self.dataset_dir):
            file_path = os.path.join(self.dataset_dir, filename)

            if not os.path.isfile(file_path) or not filename.lower().endswith((".html", ".htm")):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    html_content = file.read()
                    self._process_ship_html(html_content)
            except Exception as e:
                print(f"[ERROR]: Failed to parse {filename}: {e}")
                return EmbeddingPipeline.FAILURE
        
        return EmbeddingPipeline.SUCCESS

    def _process_ship_html(self, html_content: str):
        processor = ShipHTMLProcessor(html_content)
        raw_chunks = processor.extract_chunks()
        optimized_chunks = ChunkStrategy.split_chunks(raw_chunks)
        self.vdb.add(optimized_chunks, SHIPS_COLLECTION_NAME)

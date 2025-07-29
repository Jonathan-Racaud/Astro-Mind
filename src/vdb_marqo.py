import marqo
import os
import json

from marqo.errors import MarqoWebError

from src.vdb import VectorDB
from src.constants import *
from src.utilities import is_dir_empty

class MarqoVDB(VectorDB):
    def __init__(self, uri):
        super().__init__()

        self.client = marqo.Client(url=uri)
        self.embedding_model = "hf/e5-base-v2"
        self.ship_index = "ships"

    def _load_ships_data(self, force=False):
        transformed_data_dir = f"{SHIPS_DATA_DIR}/transformed_data"
    
        if is_dir_empty(f"{transformed_data_dir}"):
            print("[ERROR]: No available extracted ship data to process")
            return

        mappings = {
            "combination_field": {
                "type": "multimodal_combination",
                "weights": {"text": 0.8, "metadata": 0.2}
            }
        }

        index_creation_result = None
        try:
            if self.client.get_index(self.ship_index):
                if force:
                    self.client.delete_index(self.ship_index)
                    index_creation_result = self.client.create_index(self.ship_index, model=self.embedding_model)
        except MarqoWebError as e:
            if e.code == "index_not_found":
                index_creation_result = self.client.create_index(self.ship_index, model=self.embedding_model)

        if index_creation_result == None:
            return

        print("[INFO]: Started ship data loading process.")

        for filename in os.listdir(transformed_data_dir):
            file_path = os.path.join(transformed_data_dir, filename)

            # Skip directories or non-JSON files
            if not os.path.isfile(file_path) or not filename.lower().endswith((".json", ".jsonl")):
                continue

            with open(file_path, "r") as ship_file:
                ship_lines = ship_file.readlines()

                ship_document = []

                # I'm only extracting the "text" from the transformed data because I have yet to understand
                # how to index the metadata with it. Marqo raises an error and asks for mappings, but I do not
                # understand what exact mapping I need to use. Tried this, but it didn't work:
                #
                # mappings = {
                #     "entity_name": {"type": "text_field", "language": "en"},
                #     "document_type": {"type": "text_field", "language": "en"},
                #     "chunk_type": {"type": "text_field", "language": "en"}
                # } 
                #
                # Then called like this: mq.index(index).add_documents(ship_document, tensor_fields=["text"], mappings=mappings)
                for line in ship_lines:
                    text = json.loads(line)["text"]
                    ship_document.append({"text": text})

                self.client.index(self.ship_index).add_documents(ship_document, tensor_fields=["text"], mappings=mappings)
        
        print("[INFO]: Ship data loading process complete.")
 
    def get_context_for_ships(self, question):
        results = self.client.index(self.ship_index).search(
            q=question,
            limit=3
        )

        context = ""
        for hit in results["hits"]:
            text = hit["text"]
            context += f"{text}\n"

        return context
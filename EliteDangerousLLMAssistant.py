import os
import json
import re

from dataclasses import asdict

from langchain_mistralai import ChatMistralAI as Chat
# from langchain_openai import ChatOpenAI as Chat
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate
)

from src.extract_ship import extract_ship_data

# --- Constants --- #
DATASET_DIR = "dataset"
SHIPS_DATA_DIR = f"{DATASET_DIR}/Ships"
EQUIPMENT_DATA_DIR = f"{DATASET_DIR}/Equipments"
WEAPON_DATA_DIR = f"{DATASET_DIR}/Weapons"
ENGINEERING_DATA_DIR = f"{DATASET_DIR}/Engineering"
OUTPUT_DIR = "output"

API_KEY = "MISTRAL_API_KEY"
AI_MODEL = "mistral-small-latest"
API_KEY_NOT_FOUND_ERROR = "API_KEY_NOT_FOUND_ERROR"

# OPENAI_API_BASE_URL = "http://192.168.50.77:1234/v1"

os.environ[API_KEY] = os.getenv(API_KEY) or API_KEY_NOT_FOUND_ERROR
# os.environ["OPENAI_API_BASE_URL"] = OPENAI_API_BASE_URL
# os.environ["OPENAI_API_KEY"] = API_KEY

# --- Utilities --- #
def is_dir_empty(path: str) -> bool:
    return not os.listdir(path)

def normalize_str(s: str) -> str:
    return '-'.join(re.sub(r'\W+', ' ', s.lower()).strip().split())

# --- Extraction --- #
def extract_ships_data(force=False):
    raw_data_dir = f"{SHIPS_DATA_DIR}/raw_data"
    extracted_data_dir = f"{SHIPS_DATA_DIR}/extracted_data"
    
    if not is_dir_empty(f"{extracted_data_dir}") and not force:
        print("[INFO]: Found extracted ship data. Skipping extraction process.")
        return
    
    if is_dir_empty(f"{raw_data_dir}"):
        print("[ERROR]: No available raw ship data to process")
        return

    print("[INFO]: Starting ship data extraction process")
    for filename in os.listdir(raw_data_dir):
        file_path = os.path.join(raw_data_dir, filename)

        # Skip directories or non-HTML files
        if not os.path.isfile(file_path) or not filename.lower().endswith((".html", ".htm")):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                raw_html_doc = file.read()
                ship_data = extract_ship_data(raw_html_doc)
        
                normalized_name = normalize_str(ship_data.name)
                print(f"[INFO]: Extracted data for {ship_data.name}")
                with open(f"{extracted_data_dir}/ship_{normalized_name}_extracted_data.json", "w") as ship_json_file:
                    json.dump(asdict(ship_data), ship_json_file)
        except Exception as e:
            print(f"[!] Failed to extract data for {filename}: {e}")
    
    print("[INFO]: Ship data extraction completed.")

def extract(force=False):
    extract_ships_data(force)

# --- Transform --- #
def chunkify(json_data):
    # llm = Chat(
    #     api_key=API_KEY,
    #     base_url=OPENAI_API_BASE_URL,
    #     temperature=0.5,
    #     model=AI_MODEL
    # )
    llm = Chat(temperature=0.5, model=AI_MODEL)

    # This does not work with mistralai/mistral-7b-instruct-v0.3
    system_prompt = SystemMessagePromptTemplate.from_template("""You are an expert in summarizing raw information into natural language.
    You will take raw json data and generate chunks to be embedded in a vector database. 
    """)
    
    user_prompt = HumanMessagePromptTemplate.from_template(
        """You are tasked with transforming structured JSON data into clear, natural-language chunks suitable for embedding into a vector database.
        Each JSON object describes a component (e.g., ship, weapon, equipment). Extract its information and convert it into compact, human-readable descriptions. Group related facts together. Use the JSONL format shown below.

        ---

        {json}

        ---
        
        Here is an example of the expected output.

        {{"text": "The Python Mk II is a multirole ship manufactured by Faulcon DeLacy...", "metadata": {{"entity_name": "Python Mk II", "document_type": "ship", "chunk_type": "overview"}}}}
        {{"text": "The Python Mk II has an armor rating of 480 and shields of 540 MJ.", "metadata": {{"entity_name": "Python Mk II", "document_type": "ship", "chunk_type": "specifications"}}}}
        {{"text": "The Shield Booster (Class 0, Grade A) provides a 20% shield boost.", "metadata": {{"entity_name": "Shield Booster", "document_type": "equipment", "class": "0", "rating": "A"}}}}
        {{"text": "The Guardian Shard Cannon deals thermal damage with 74.5 DPS...", "metadata": {{"entity_name": "Guardian Shard Cannon", "document_type": "weapon", "damage_type": "Thermal", "dps": 74.5}}}}

        Instructions:
        - Use **ONLY** the data from the provided json.
        - Output in plain text.
        - Only output the JSONL lines
        - Do not include any explanation, additional context or code fences.
        """)

    # system_prompt cannot be used with mistral-7b-instruct
    prompt = ChatPromptTemplate.from_messages([system_prompt, user_prompt])

    chain = (
        {
            "json": lambda x: x["json"]
        }
        | prompt
        | llm
        | {"chunks": lambda x: x.content}
    )

    response = chain.invoke({"json": json_data})
    chunks = response["chunks"]

    return chunks

def transform_ship_data(force=False):
    extracted_data_dir = f"{SHIPS_DATA_DIR}/extracted_data"
    transformed_data_dir = f"{SHIPS_DATA_DIR}/transformed_data"
    
    if not is_dir_empty(f"{transformed_data_dir}") and not force:
        print("[INFO]: Found transformed ship data. Skipping transformation process.")
        return
    
    if is_dir_empty(f"{extracted_data_dir}"):
        print("[ERROR]: No available extracted ship data to process")
        return
    
    print("[INFO]: Started ship data transformation process.")
    for filename in os.listdir(extracted_data_dir):
        file_path = os.path.join(extracted_data_dir, filename)

        # Skip directories or non-JSON files
        if not os.path.isfile(file_path) or not filename.lower().endswith((".json")):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                ship_json_data = file.read()
                normalized_name = filename.split('_', 2)[1]

                print(f"[INFO]: Transforming data for {normalized_name}")

                transformed_data = chunkify(ship_json_data)

                with open(f"{transformed_data_dir}/ship_{normalized_name}_transformed_data.json", "w") as transformed_json_file:
                    transformed_json_file.write(transformed_data)
        except Exception as e:
            print(f"[!] Failed to transform data for {filename}: {e}")
    
    print("[INFO]: Ship data transformation completed.")

def transform(force=False): 
    transform_ship_data(force)

# --- Main --- #
def main():
    extract()
    transform()
    #load()

if __name__ == "__main__":
    main()

import os
import json
import re
import streamlit as st
import marqo

from marqo.errors import MarqoWebError

from dataclasses import asdict

from langchain_mistralai import ChatMistralAI as Chat
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate
)
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient
from tqdm import tqdm

from huggingface_hub import InferenceClient

from src.extract_ship import extract_ship_data

# --- Constants --- #
DATASET_DIR = "dataset"
SHIPS_DATA_DIR = f"{DATASET_DIR}/Ships"
EQUIPMENT_DATA_DIR = f"{DATASET_DIR}/Equipments"
WEAPON_DATA_DIR = f"{DATASET_DIR}/Weapons"
ENGINEERING_DATA_DIR = f"{DATASET_DIR}/Engineering"
OUTPUT_DIR = "output"

ELITE_DANGEROUS_VECTOR_DB = "./elite_dangerous_llm_assistant.db"
COLLECTION_NAME = "rag_collection"

API_KEY = "MISTRAL_API_KEY"
AI_MODEL = "mistral-small-latest"
API_KEY_NOT_FOUND_ERROR = "API_KEY_NOT_FOUND_ERROR"
ELITE_HF_TOKEN = "ELITE_DANGEROUS_LLM_ASSISTANT_HF_TOKEN"

os.environ[API_KEY] = os.getenv(API_KEY) or API_KEY_NOT_FOUND_ERROR
os.environ["HF_TOKEN"] = os.getenv(ELITE_HF_TOKEN) or API_KEY_NOT_FOUND_ERROR

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

# --- Load --- #
def metadata_extractor(record: dict, metadata: dict) -> dict:
    # 'record' is the full JSON object for a single line (or the result of the jq_schema)
    # 'metadata' contains default metadata like 'source' and 'seq_num'

    # Add your custom metadata fields
    if 'metadata' in record and isinstance(record['metadata'], dict):
        metadata['entity_name'] = record['metadata'].get('entity_name')
        metadata['document_type'] = record['metadata'].get('document_type')
        metadata['chunk_type'] = record['metadata'].get('chunk_type')
    return metadata

def emb_text(text):
    embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return embedding_model.encode([text], normalize_embedding=True).tolist()[0]

def load_ships_data_milvus(force=False):
    milvus_client = MilvusClient(uri=ELITE_DANGEROUS_VECTOR_DB)
    milvus_has_collection = milvus_client.has_collection(COLLECTION_NAME)

    if milvus_has_collection and not force:
        print("[INFO]: Vector database already created. Skipping ship data loading process.")
        return
    elif milvus_has_collection and force:
        milvus_client.drop_collection(COLLECTION_NAME)

    transformed_data_dir = f"{SHIPS_DATA_DIR}/transformed_data"
    
    if is_dir_empty(f"{transformed_data_dir}"):
        print("[ERROR]: No available extracted ship data to process")
        return
    
    print("[INFO]: Started ship data loading process.")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    milvus_client.create_collection(
        collection_name=COLLECTION_NAME,
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
            metadata_func=metadata_extractor
        )

        docs = loader.load()
        chunks = text_splitter.split_documents(docs)

        text_lines = [chunk.page_content for chunk in chunks]

        data = []
        for i, line in enumerate(tqdm(text_lines)):
            data.append({"id": i, "vector": emb_text(line), "text": line})
        
        milvus_client.insert(
            collection_name=COLLECTION_NAME,
            data=data
        )

def load_ships_data_marqo(force=False):
    if not force: return

    transformed_data_dir = f"{SHIPS_DATA_DIR}/transformed_data"
    
    if is_dir_empty(f"{transformed_data_dir}"):
        print("[ERROR]: No available extracted ship data to process")
        return
    
    print("[INFO]: Started ship data loading process.")

    mq = marqo.Client(url="http://localhost:8882")

    index = "ships"
    model = "hf/e5-base-v2"
    # mappings = {
    #     "entity_name": {"type": "text_field", "language": "en"},
    #     "document_type": {"type": "text_field", "language": "en"},
    #     "chunk_type": {"type": "text_field", "language": "en"}
    # }

    mappings = {
        "combination_field": {
            "type": "multimodal_combination",
            "weights": {"text": 0.8, "metadata": 0.2}
        }
    }

    try:
        if mq.get_index(index):
            mq.delete_index(index)
            index_creation_result = mq.create_index(index, model=model)
    except MarqoWebError as e:
        if e.code == "index_not_found":
            index_creation_result = mq.create_index(index, model=model)
    
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

            mq.index(index).add_documents(ship_document, tensor_fields=["text"], mappings=mappings)

db_used = None

def load_milvus(force=False):
    db_used = "milvus"
    load_ships_data_milvus(force)

def load_marqo(force=False):
    db_used = "marqo"
    load_ships_data_marqo(force)

# --- LLM --- #
def get_context_milvus(question):
    milvus_client = MilvusClient(uri=ELITE_DANGEROUS_VECTOR_DB)

    db_search = milvus_client.search(
        collection_name=COLLECTION_NAME,
        data=[emb_text(question)],
        limit=3,
        search_params={"metric_type": "IP", "params": {}},
        output_fields=["text"]
    )

    retrieved_db_search = [(res["entity"]["text"], res["distance"]) for res in db_search[0]]

    context = "\n".join([db_res[0] for db_res in retrieved_db_search])

    return context

def get_context_marqo(question):
    mq = marqo.Client(url="http://localhost:8882")

    index = "ships"
    
    results = mq.index(index).search(
        q=question,
        limit=3
    )

    context = ""
    for hit in results["hits"]:
        text = hit["text"]
        context += f"{text}\n"

    return context

def ask_llm(question):
    if db_used == "milvus":
        context = get_context_milvus(question)
    elif db_used == "marqo":
        context = get_context_marqo(question)

    prompt = """
    Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.

    <context>
    {context}
    </context>

    <question>
    {question}
    </question>

    Also provide the sources used for your answer.
    """

    llm = InferenceClient(provider="hf-inference", api_key=os.environ[ELITE_HF_TOKEN])
    prompt = prompt.format(context=context, question=question)

    completion = llm.chat.completions.create(
        model="HuggingFaceTB/SmolLM3-3B",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    clean_content = re.sub(r'<think>.*?</think>\s*', '', completion.choices[0].message.content, flags=re.DOTALL)

    return clean_content

# --- Chat UI --- #
def chat_ui():
    st.title("Elite Dangerous AI Assistant")
    st.write("This chatbot is there to help you get information about the different ships of Elite Dangerous")

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    for message in st.session_state.conversation_history:
        with st.chat_message("user" if message.startswith("User:") else "assistant"):
            st.markdown(message.replace("User: ", "").replace("Assistant: ", ""))

    user_query = st.chat_input("Hello commander, how can I help you today?")

    if user_query:
        with st.chat_message("user"):
            st.markdown(user_query)
        
        st.session_state.conversation_history.append(f"User: {user_query}")

        response = ask_llm(user_query)

        st.session_state.conversation_history.append(f"Assistant: {response}")

        with st.chat_message("assistant"):
            st.markdown(response)

# --- Main --- #
def main():
    extract()
    transform()
    load_milvus()
    #load_marqo(False)
    chat_ui()

if __name__ == "__main__":
    main()

import os
import json
import re
import streamlit as st

from dataclasses import asdict

from dotenv import load_dotenv

from src.extract_ship import extract_ship_data

from src.vdb import VectorDB
from src.vdb_qdrant import QdrantVectorDB
from src.embedder import BAAIEmbedder

from src.llm import LLM
from src.llm_huggingface import HuggingFaceLLM
from src.llm_mistral import MistralLLM
from src.llm_openrouter import OpenRouterLLM
from src.llm_local import LocalLLM

from src.constants import *
from src.utilities import is_dir_empty, normalize_str

#=== Extract ===#
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

#=== Transform ===#
def transform_ship_data(llm: LLM, force=False):
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

                transformed_data = llm.ask(query=ship_json_data)

                with open(f"{transformed_data_dir}/ship_{normalized_name}_transformed_data.json", "w") as transformed_json_file:
                    transformed_json_file.write(transformed_data)
        except Exception as e:
            print(f"[!] Failed to transform data for {filename}: {e}")
    
    print("[INFO]: Ship data transformation completed.")

def transform(llm: LLM, force=False): 
    transform_ship_data(llm, force)

#=== Ask ===#
def chat_ui(llm: LLM, vdb: VectorDB):
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

        # This llm helps in getting additional information from the question such as which ship exactly has been queried?
        helper_llm = LocalLLM(
            provider=os.getenv(INFERENCE_LLM_PROVIDER),
            api_key=os.getenv(INFERENCE_LLM_API_KEY),
            model="liquid/lfm2-1.2b",
            url=os.getenv(INFERENCE_LLM_URL)
        )
        helper_llm.system_prompt = """From the provided <context></context>, retrieve the name of the ship the query's topic revolves around. 
        If none can be found, assume that the user talks of the previously mentionned ship.
        
        <context>
        {context}
        </context>

        Return only the name of the ship. No other information. If no ship can be found return "N/A"
        """
        ship_name = helper_llm.ask(user_query, "")

        context = vdb.get_context(user_query, ship_name if ship_name != "N/A" else None)
        response = llm.ask(context, user_query)

        st.session_state.conversation_history.append(f"Assistant: {response}")

        with st.chat_message("assistant"):
            st.markdown(response)

#=== Setup ===#
def setup_environment():
    if "env_setup" in st.session_state:
        return

    load_dotenv()

    os.environ["HF_TOKEN"] = os.getenv(EMBEDDER_LLM_API_KEY)

    st.session_state["env_setup"] = True

def setup_inference_llm():
    inference_llm = LocalLLM(
        provider=os.getenv(INFERENCE_LLM_PROVIDER),
        api_key=os.getenv(INFERENCE_LLM_API_KEY),
        model=os.getenv(INFERENCE_LLM_MODEL),
        url=os.getenv(INFERENCE_LLM_URL)
    )

    inference_llm.system_prompt = """
    Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.

    <context>
    {context}
    </context>

    <question>
    {query}
    </question>

    Also only provide the sources from the context used for your answer.
    """

    return inference_llm

def setup_transform_llm():
    transform_llm = MistralLLM(
        provider=os.getenv(TRANSFORM_LLM_PROVIDER),
        api_key=os.getenv(TRANSFORM_LLM_API_KEY),
        model=os.getenv(TRANSFORM_LLM_MODEL)
    )

    transform_llm.system_prompt = """You are an expert in summarizing raw information into natural language.
    You will take raw json data and generate chunks to be embedded in a vector database. 
    """

    transform_llm.user_prompt = """You are tasked with transforming structured JSON data into clear, natural-language chunks suitable for embedding into a vector database.
        Each JSON object describes a component (e.g., ship, weapon, equipment). Extract its information and convert it into compact, human-readable descriptions. Group related facts together. Use the JSONL format shown below.

        ---

        {query}

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
        """
    
    return transform_llm

def setup_llm():
    if "llm_setup" in st.session_state:
        return st.session_state["llm_setup"]

    transform_llm = setup_transform_llm()
    inference_llm = setup_inference_llm()

    st.session_state["llm_setup"] = (transform_llm, inference_llm)

    return (transform_llm, inference_llm)

def setup_vector_db():
    if "vector_db_setup" in st.session_state:
        return st.session_state["vector_db_setup"]
    
    embedder = BAAIEmbedder()
    vector_db: VectorDB = QdrantVectorDB(embedder=embedder)

    st.session_state["vector_db_setup"] = vector_db

    return vector_db
    

#=== Main ===#
def main():
    #--- Setup ---#
    setup_environment()
    (transform_llm, inference_llm) = setup_llm()
    vector_db = setup_vector_db()

    #--- Extract ---#
    extract()

    #--- Transform ---#
    transform(transform_llm)

    #--- Load ---#
    vector_db.load()

    #--- Ask ---#
    chat_ui(inference_llm, vector_db)

if __name__ == "__main__":
    main()

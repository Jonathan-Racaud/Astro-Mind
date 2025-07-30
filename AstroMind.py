import os
import streamlit as st

from typing import List
from dotenv import load_dotenv

from src.constants import *

from src.vdb import VectorDB
from src.vdb_qdrant import QdrantVectorDB

from src.llm import LLM
from src.llm_local import LocalLLM

from src.embedder import Embedder, BAAIEmbedder

from src.embedding_pipeline import EmbeddingPipeline

from src.ships.ships_embedding_pipeline import ShipsEmbeddingPipeline

#=== Ask ===#
def chat_ui(llm: LLM, vdb: VectorDB, pipelines: List[EmbeddingPipeline]):
    st.title("Astro Mind")
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

        topic = ""
        if 'topic' not in st.session_state:
            topic = llm.ask(
                user_query,
                """What ship are they talking about?
                Reply only with the name of the ship using the following format:
                
                The query relates to the ship: <shipname>.
                
                Replace <shipname> by the actual shipname the user are talking about.
                """
            )
            st.session_state.topic = topic
        else:
            topic = st.session_state.topic

        context = vdb.search(f"{user_query}\n{topic}", SHIPS_COLLECTION_NAME)
        context.append(topic)

        response = llm.ask(context, user_query)

        st.session_state.conversation_history.append(f"Assistant: {response}")

        with st.chat_message("assistant"):
            st.markdown(response)
    
    with st.sidebar:
        st.header("Debug", divider=True)
        def run_pipelines():
            for pipeline in pipelines:
                result = pipeline.start()

                if result == EmbeddingPipeline.FAILURE:
                    st.error(f"Failed to embed the dataset")
        
        st.button(
            "Embed documents",
            on_click=run_pipelines,
            key="embed_button"
        )
        
        # Add reset button
        if st.button("⚠️ Reset All Resources", key="reset_button"):
            # Clear cached resources
            st.cache_resource.clear()
            # Close vector database connection
            if hasattr(vdb, 'close'):
                vdb.close()
            # Clear session state
            st.session_state.clear()
            # Rerun the app to reinitialize resources
            st.rerun()

def ui(pipelines: List[EmbeddingPipeline], llm: LLM, vdb: VectorDB):
    chat_ui(llm, vdb, pipelines)

#=== Setup ===#
def setup_environment():
    if "env_setup" in st.session_state:
        return

    load_dotenv()

    os.environ["HF_TOKEN"] = os.getenv(EMBEDDER_LLM_API_KEY)

    st.session_state["env_setup"] = True

@st.cache_resource
def setup_inference_llm():
    inference_llm = LocalLLM(
        provider=os.getenv(INFERENCE_LLM_PROVIDER),
        api_key=os.getenv(INFERENCE_LLM_API_KEY),
        model=os.getenv(INFERENCE_LLM_MODEL),
        url=os.getenv(INFERENCE_LLM_URL)
    )

    inference_llm.user_prompt = """
    Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.

    <context>
    {context}
    </context>

    <question>
    {query}
    </question>
    """

    return inference_llm

@st.cache_resource
def setup_llm():
    inference_llm = setup_inference_llm()
    return inference_llm

@st.cache_resource
def setup_vector_db():
    vector_db: VectorDB = QdrantVectorDB(embedder=BAAIEmbedder(), db_path=LOCAL_VECTOR_DB_FILE)
    return vector_db

#=== Main ===#
def main():
    #--- Setup ---#
    setup_environment()
    
    try:
        vdb = setup_vector_db()
        llm = setup_llm()
    except RuntimeError as e:
        st.error(f"Resource conflict error: {str(e)}")
        st.error("Please reset the resources using the 'Reset All Resources' button.")
        # Show only the reset button
        if st.button("⚠️ Reset All Resources"):
            st.cache_resource.clear()
            st.session_state.clear()
            st.rerun()
        return

    #--- Embedding ---#
    ships_embedding_pipeline = ShipsEmbeddingPipeline(vdb)

    #--- Ask ---#
    ui(
        [ships_embedding_pipeline],
        llm,
        vdb
    )

if __name__ == "__main__":
    main()

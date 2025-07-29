from src.llm import LLM

from langchain_mistralai import ChatMistralAI as Chat
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate
)

class MistralLLM(LLM):
    def __init__(self, provider, api_key, model, url=None):
        super().__init__(provider, api_key, model, url)

        self.llm = Chat(
            api_key=self.api_key,
            model=self.model,
            temperature=0.5
        )

    def ask(self, context, query):
        system_prompt = SystemMessagePromptTemplate.from_template(self.system_prompt)
        user_prompt = HumanMessagePromptTemplate.from_template(self.user_prompt)

        prompt = ChatPromptTemplate.from_messages([system_prompt, user_prompt])

        chain = (
            {
                "context": lambda x: x["context"],
                "query": lambda x: x["query"]
            }
            | prompt
            | self.llm
            | { "chunks": lambda x: x.content }
        )

        response = chain.invoke({"context": context, "query": query})
        chunks = response["chunks"]

        return chunks

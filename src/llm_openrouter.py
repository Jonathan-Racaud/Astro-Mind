from src.llm import LLM

from langchain_openai.chat_models import ChatOpenAI as Chat
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate
)

class OpenRouterLLM(LLM):
    def __init__(self, provider, api_key, model, url):
        super().__init__(provider, api_key, model, url)

        self.llm = Chat(
            api_key=self.api_key,
            model=self.model,
            base_url=self.url,
            temperature=0.5
        )

    def ask(self, context, query):
        system_prompt = ""
        if self.system_prompt is str:
            system_prompt = SystemMessagePromptTemplate.from_template(self.system_prompt)

        user_prompt = ""
        if self.user_prompt is str:
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

        response = chain.invoke({"query": query, "context": context})
        chunks = response["chunks"]

        return chunks

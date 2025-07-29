from src.llm import LLM

from langchain_openai.chat_models import ChatOpenAI as Chat
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate
)

class LocalLLM(LLM):
    def __init__(self, provider, api_key, model, url):
        super().__init__(provider, api_key, model, url)

        self.llm = Chat(
            api_key="lm-studio",
            model=self.model,
            base_url=self.url,
            temperature=0.5
        )

    def ask(self, context, query):
        messages = []
        if isinstance(self.system_prompt, str):
            messages.append(SystemMessagePromptTemplate.from_template(self.system_prompt))
        if isinstance(self.user_prompt, str):
            messages.append(HumanMessagePromptTemplate.from_template(self.user_prompt))

        prompt = ChatPromptTemplate.from_messages(messages)

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

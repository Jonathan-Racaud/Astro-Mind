from openai import OpenAI

from src.llm import LLM

class LocalLLM(LLM):
    def __init__(self, provider, api_key, model, url):
        super().__init__(provider, api_key, model, url)

        self.llm = OpenAI(
            api_key=self.api_key,
            base_url=url
        )

    def ask(self, context, query):
        prompt = "".join([
            self.system_prompt or "", 
            "\n",
            self.user_prompt or ""]
        ).format(context=context, query=query)
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5
        )

        return response.choices[0].message.content
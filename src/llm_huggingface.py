from src.llm import LLM
import re

from huggingface_hub import InferenceClient

class HuggingFaceLLM(LLM):
    def __init__(self, provider, api_key, model):
        super().__init__(provider, api_key, model)
        
        self.llm = InferenceClient(
            provider=self.provider,
            api_key=self.api_key
        )

    def ask(self, context, query):
        prompt = prompt.format(context, query)

        completion = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        clean_content = re.sub(r'<think>.*?</think>\s*', '', completion.choices[0].message.content, flags=re.DOTALL)

        return clean_content
import json

from openai import OpenAI

from src.config import get_llm_config


class LLMConfigurationError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, client=None):
        self.config = get_llm_config()
        if not self.config.api_key or self.config.api_key.startswith("your_"):
            raise LLMConfigurationError("LLM_API_KEY is not configured.")
        self.client = client or OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)

    def generate(self, system_prompt, user_prompt):
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise ValueError("The LLM returned an empty response.")
        if content.startswith("```"):
            content = content.removeprefix("```json").removeprefix("```")
            content = content.removesuffix("```").strip()
        return json.loads(content)

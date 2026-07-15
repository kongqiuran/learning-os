import logging
import re

from openai import OpenAI

from src.config import get_llm_config
from src.ai.utils.json_parser import parse_llm_json


logger = logging.getLogger(__name__)


class LLMConfigurationError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, client=None):
        self.config = get_llm_config()
        if not self.config.api_key or self.config.api_key.startswith("your_"):
            raise LLMConfigurationError("LLM_API_KEY is not configured.")
        self.client = client or OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)

    def generate(self, system_prompt, user_prompt, stage="unknown"):
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
        try:
            result = parse_llm_json(content)
            if not isinstance(result, dict):
                raise ValueError("The LLM JSON root must be an object.")
            return result
        except (TypeError, ValueError) as exc:
            logger.error(
                "LLM JSON processing failed: %s",
                {
                    "stage": stage,
                    "error": type(exc).__name__,
                    "preview": _safe_response_preview(content),
                },
            )
            raise


def _safe_response_preview(content):
    preview = " ".join(content[:500].split())
    preview = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[redacted-email]", preview)
    preview = re.sub(
        r"(?i)(api[_ -]?key|authorization|bearer)\s*[:=]?\s*[\w.-]+",
        r"\1 [redacted]",
        preview,
    )
    return preview

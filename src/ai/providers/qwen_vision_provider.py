import base64
import json
import time
from pathlib import Path

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

from src.ai.prompt_manager import get_prompt
from src.ai.providers.base import VisionAnalysis, VisionProvider
from src.ai.utils.json_parser import parse_llm_json
from src.config import VisionConfig, get_vision_config
from src.logging_config import get_logger


logger = get_logger(__name__)
RETRYABLE_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)


class QwenVisionProvider(VisionProvider):
    def __init__(self, client=None, config: VisionConfig | None = None, sleep_fn=None):
        self.config = config or get_vision_config()
        self._client = client
        self.sleep_fn = sleep_fn or time.sleep

    @property
    def provider_name(self):
        return "qwen"

    @property
    def model_name(self):
        return self.config.model

    def is_available(self):
        return bool(
            self.config.enabled
            and self.config.provider == self.provider_name
            and self.config.api_key
            and not self.config.api_key.startswith("your_")
            and self.config.base_url
            and self.config.model
        )

    def analyze_page(self, image_path: Path, page_text: str, metadata: dict):
        if not self.is_available():
            raise RuntimeError("Qwen vision provider is not configured.")

        client = self._client or OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            max_retries=0,
        )
        image_url = _image_data_url(Path(image_path))
        user_text = json.dumps(
            {
                "page_text": str(page_text or "")[:12000],
                "metadata": metadata,
            },
            ensure_ascii=False,
        )
        messages = [
            {"role": "system", "content": get_prompt("page_vision_analyzer")},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ]
        last_error = None
        for attempt in range(self.config.max_attempts):
            try:
                response = client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=0.1,
                    timeout=self.config.timeout_seconds,
                )
                content = (response.choices[0].message.content or "").strip()
                parsed = parse_llm_json(content)
                if not isinstance(parsed, dict):
                    raise ValueError("Vision response JSON root must be an object.")
                usage = getattr(response, "usage", None)
                return VisionAnalysis(
                    content=_normalize_vision_result(parsed),
                    provider=self.provider_name,
                    model=self.config.model,
                    input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
                    output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
                )
            except RETRYABLE_ERRORS as exc:
                last_error = exc
                if attempt + 1 < self.config.max_attempts:
                    self.sleep_fn(min(2 ** attempt, 4))
                    continue
                raise
            except Exception:
                raise
        raise RuntimeError("Qwen vision request failed.") from last_error


def _image_data_url(image_path):
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _normalize_vision_result(result):
    try:
        important_level = int(result.get("important_level", 1))
    except (TypeError, ValueError):
        important_level = 1
    try:
        confidence = float(result.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    return {
        "title": str(result.get("title", "")).strip()[:500],
        "summary": str(result.get("summary", "")).strip()[:4000],
        "important_level": max(1, min(5, important_level)),
        "key_points": _as_list(result.get("key_points")),
        "formulas": _as_list(result.get("formulas")),
        "figures": _as_list(result.get("figures")),
        "exam_points": _as_list(result.get("exam_points")),
        "teacher_emphasis": _as_list(result.get("teacher_emphasis")),
        "evidence": _as_list(result.get("evidence")),
        "confidence": max(0.0, min(1.0, confidence)),
    }


def _as_list(value):
    if value is None or value == "":
        return []
    items = value if isinstance(value, list) else [value]
    return [_bounded_value(item) for item in items[:30]]


def _bounded_value(value):
    if isinstance(value, dict):
        return {
            str(key)[:120]: _bounded_value(item)
            for key, item in list(value.items())[:20]
        }
    if isinstance(value, list):
        return [_bounded_value(item) for item in value[:20]]
    if isinstance(value, str):
        return value[:2000]
    return value

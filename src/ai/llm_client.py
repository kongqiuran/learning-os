import logging
import re
import time

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError

from src.ai.utils.json_parser import LLMJSONParseError, parse_llm_json
from src.config import get_llm_config


logger = logging.getLogger(__name__)
RETRY_DELAYS_SECONDS = (2, 5, 10)
JSON_CORRECTION_PROMPT = """Your previous response was not valid JSON.

Generate the complete response again.

Requirements:
1. Output JSON only.
2. Do not use markdown.
3. Do not add explanations or comments.
4. Use double quotes and valid JSON escaping.
5. Complete every object and array."""
RETRYABLE_NETWORK_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)


class LLMConfigurationError(RuntimeError):
    pass


class LLMGenerationError(RuntimeError):
    def __init__(
        self,
        message,
        *,
        stage,
        retry_count,
        error_type,
        response_preview=None,
    ):
        super().__init__(message)
        self.stage = stage
        self.retry_count = retry_count
        self.error_type = error_type
        self.response_preview = response_preview


class LLMClient:
    def __init__(self, client=None, progress_callback=None, sleep_fn=None):
        self.config = get_llm_config()
        if not self.config.api_key or self.config.api_key.startswith("your_"):
            raise LLMConfigurationError("LLM_API_KEY is not configured.")
        self.client = client or OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            max_retries=0,
        )
        self.progress_callback = progress_callback
        self.sleep_fn = sleep_fn or time.sleep

    def generate(self, system_prompt, user_prompt, stage="unknown"):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        for attempt_index in range(self.config.max_attempts):
            self._notify_progress(stage, attempt_index)
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=0.2,
                    timeout=self.config.timeout_seconds,
                )
            except RETRYABLE_NETWORK_ERRORS as exc:
                if attempt_index + 1 >= self.config.max_attempts:
                    raise LLMGenerationError(
                        "The model request failed after limited network retries.",
                        stage=stage,
                        retry_count=attempt_index,
                        error_type=type(exc).__name__,
                    ) from exc
                self._log_retry(stage, attempt_index, type(exc).__name__)
                self._wait_before_retry(attempt_index)
                continue
            except Exception as exc:
                raise LLMGenerationError(
                    "The model request failed without a retryable network error.",
                    stage=stage,
                    retry_count=attempt_index,
                    error_type=type(exc).__name__,
                ) from exc

            content = (response.choices[0].message.content or "").strip()
            if not content:
                parse_error = LLMJSONParseError("The LLM returned an empty response.")
            else:
                try:
                    result = parse_llm_json(content)
                    if not isinstance(result, dict):
                        raise LLMJSONParseError("The LLM JSON root must be an object.")
                    return result
                except LLMJSONParseError as exc:
                    parse_error = exc

            preview = _safe_response_preview(content)
            logger.warning(
                "LLM JSON processing failed; a bounded retry may follow: %s",
                {
                    "stage": stage,
                    "attempt": attempt_index + 1,
                    "max_attempts": self.config.max_attempts,
                    "error": type(parse_error).__name__,
                    "preview": preview,
                },
            )
            if attempt_index + 1 >= self.config.max_attempts:
                raise LLMGenerationError(
                    str(parse_error),
                    stage=stage,
                    retry_count=attempt_index,
                    error_type="JSONParseError",
                    response_preview=preview,
                ) from parse_error

            messages.extend(
                [
                    {"role": "assistant", "content": content},
                    {"role": "user", "content": JSON_CORRECTION_PROMPT},
                ]
            )

        raise AssertionError("The bounded LLM attempt loop exited unexpectedly.")

    def _notify_progress(self, stage, retry_count):
        if self.progress_callback is not None:
            self.progress_callback(stage=stage, retry_count=retry_count)

    def _wait_before_retry(self, attempt_index):
        delay = RETRY_DELAYS_SECONDS[min(attempt_index, len(RETRY_DELAYS_SECONDS) - 1)]
        self.sleep_fn(delay)

    @staticmethod
    def _log_retry(stage, attempt_index, error_type):
        logger.warning(
            "LLM network request failed; retrying with backoff: %s",
            {
                "stage": stage,
                "attempt": attempt_index + 1,
                "error": error_type,
            },
        )


def _safe_response_preview(content):
    preview = " ".join(content[:1000].split())
    preview = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[redacted-email]", preview)
    preview = re.sub(
        r"(?i)(api[_ -]?key|authorization|bearer)\s*[:=]?\s*[\w.-]+",
        r"\1 [redacted]",
        preview,
    )
    return preview

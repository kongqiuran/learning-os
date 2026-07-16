import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.ai.llm_client import LLMClient, LLMGenerationError


class FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=response))]
        )


class FakeOpenAIClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=FakeCompletions(responses))


class RetryableTestError(RuntimeError):
    pass


def fake_config(max_attempts=3):
    return SimpleNamespace(
        api_key="test-key",
        base_url="https://example.invalid",
        model="test-model",
        timeout_seconds=45.0,
        max_attempts=max_attempts,
    )


class LLMClientRetryTest(unittest.TestCase):
    def test_invalid_json_is_corrected_on_second_attempt(self):
        api_client = FakeOpenAIClient(["not json", '{"result": "ok"}'])
        progress = []
        with patch("src.ai.llm_client.get_llm_config", return_value=fake_config()):
            client = LLMClient(
                client=api_client,
                progress_callback=lambda **value: progress.append(value),
                sleep_fn=lambda _delay: None,
            )
            result = client.generate("system", "input", stage="document_analyzer")

        self.assertEqual(result, {"result": "ok"})
        self.assertEqual(len(api_client.chat.completions.calls), 2)
        retry_messages = api_client.chat.completions.calls[1]["messages"]
        self.assertIn("not valid JSON", retry_messages[-1]["content"])
        self.assertEqual(progress[-1], {"stage": "document_analyzer", "retry_count": 1})

    def test_network_errors_use_bounded_exponential_backoff(self):
        api_client = FakeOpenAIClient(
            [RetryableTestError("network-1"), RetryableTestError("network-2"), '{"ok": true}']
        )
        delays = []
        with (
            patch("src.ai.llm_client.get_llm_config", return_value=fake_config()),
            patch("src.ai.llm_client.RETRYABLE_NETWORK_ERRORS", (RetryableTestError,)),
        ):
            client = LLMClient(client=api_client, sleep_fn=delays.append)
            result = client.generate("system", "input", stage="course_analyzer")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(delays, [2, 5])
        self.assertEqual(len(api_client.chat.completions.calls), 3)

    def test_three_invalid_outputs_raise_diagnostic_error(self):
        api_client = FakeOpenAIClient(["not json", "still invalid", "invalid again"])
        with patch("src.ai.llm_client.get_llm_config", return_value=fake_config()):
            client = LLMClient(client=api_client, sleep_fn=lambda _delay: None)
            with self.assertRaises(LLMGenerationError) as context:
                client.generate("system", "input", stage="learning_package_generator")

        error = context.exception
        self.assertEqual(error.stage, "learning_package_generator")
        self.assertEqual(error.retry_count, 2)
        self.assertEqual(error.error_type, "JSONParseError")
        self.assertIn("invalid again", error.response_preview)

    def test_timeout_is_applied_to_every_model_call(self):
        api_client = FakeOpenAIClient(['{"ok": true}'])
        with patch("src.ai.llm_client.get_llm_config", return_value=fake_config()):
            client = LLMClient(client=api_client, sleep_fn=lambda _delay: None)
            client.generate("system", "input")

        self.assertEqual(api_client.chat.completions.calls[0]["timeout"], 45.0)


if __name__ == "__main__":
    unittest.main()

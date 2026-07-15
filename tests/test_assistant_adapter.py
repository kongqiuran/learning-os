import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.api.adapters import assistant_adapter


class FakeLLMClient:
    def __init__(self, answer="课程资料中的解释"):
        self.answer = answer
        self.calls = []

    def generate(self, system_prompt, user_prompt, stage):
        self.calls.append((system_prompt, user_prompt, stage))
        return {"answer": self.answer}


class AssistantAdapterTest(unittest.TestCase):
    def test_no_course_context_returns_fixed_answer_without_model_call(self):
        client = FakeLLMClient()
        with (
            patch.object(assistant_adapter, "get_learning_package", return_value=None),
            patch.object(assistant_adapter, "_load_document_analyses", return_value=[]),
        ):
            result = assistant_adapter.answer_course_question(1, 2, "What is this?", llm_client=client)

        self.assertEqual(result.answer, assistant_adapter.INSUFFICIENT_CONTEXT_ANSWER)
        self.assertEqual(result.source_files, [])
        self.assertEqual(client.calls, [])

    def test_current_section_is_prioritized_and_context_is_bounded(self):
        package = SimpleNamespace(
            status="completed",
            content_json={
                "chapter_summary": "A" * 3000,
                "formula_book": "F" * 3000,
            },
        )
        client = FakeLLMClient()
        with (
            patch.object(assistant_adapter, "get_learning_package", return_value=package),
            patch.object(assistant_adapter, "get_assistant_max_context_chars", return_value=4000),
            patch.object(assistant_adapter, "_load_document_analyses", return_value=[]),
        ):
            assistant_adapter.answer_course_question(
                1,
                2,
                "Explain the formula",
                current_section="公式",
                llm_client=client,
            )

        payload = json.loads(client.calls[0][1])
        self.assertTrue(payload["course_context"].startswith("## formula_book"))
        self.assertLessEqual(len(payload["course_context"]), 4000)

    def test_document_analysis_fallback_reports_only_used_file(self):
        document = SimpleNamespace(original_filename="lecture.md")
        analysis = SimpleNamespace(summary="Core concept", topics=["Topic"], importance_map={})
        client = FakeLLMClient()
        with (
            patch.object(assistant_adapter, "get_learning_package", return_value=None),
            patch.object(
                assistant_adapter,
                "_load_document_analyses",
                return_value=[(document, analysis)],
            ),
        ):
            result = assistant_adapter.answer_course_question(1, 2, "Explain", llm_client=client)

        self.assertEqual(result.source_files, ["lecture.md"])
        self.assertEqual(result.answer, "课程资料中的解释")


if __name__ == "__main__":
    unittest.main()

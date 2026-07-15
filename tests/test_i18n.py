import json
import unittest
from pathlib import Path

from src.ai.analyzers.course_analyzer import analyze_course_documents
from src.ai.analyzers.document_analyzer import analyze_document
from src.ai.generators.learning_package_generator import generate_learning_package
from src.i18n import t


class RecordingClient:
    def __init__(self, response):
        self.response = response
        self.user_prompts = []

    def generate(self, system_prompt, user_prompt):
        self.user_prompts.append(json.loads(user_prompt))
        return self.response


class I18nTest(unittest.TestCase):
    def test_translator_defaults_to_chinese_and_switches_to_english(self):
        self.assertEqual(t("generate_package"), "生成 AI 学习包")
        self.assertEqual(t("generate_package", "en"), "Generate AI Learning Package")
        self.assertEqual(t("missing_key", "zh"), "missing_key")

    def test_application_defaults_language_state_to_chinese(self):
        app_source = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertIn('st.session_state.language = "zh"', app_source)
        self.assertIn('options=["zh", "en"]', app_source)
        self.assertIn('tr("generate_package")', app_source)
        self.assertIn('tr("course_map")', app_source)
        self.assertIn('("TEXTBOOK", "material_textbook"', app_source)
        self.assertIn('("SLIDES", "material_slides"', app_source)
        self.assertIn('("EXAM", "material_exam"', app_source)

    def test_material_inbox_labels_switch_languages(self):
        self.assertEqual(t("material_textbook", "zh"), "📘 教材")
        self.assertEqual(t("material_textbook", "en"), "📘 Textbooks")
        self.assertEqual(t("material_exam", "zh"), "📝 历年试卷")
        self.assertEqual(t("material_exam", "en"), "📝 Past Exams")
        self.assertEqual(
            t("unsupported_material_format", "zh"),
            "当前资料类型不支持该文件格式",
        )
        self.assertEqual(
            t("unsupported_material_format", "en"),
            "Unsupported file format for this material type",
        )

    def test_language_is_sent_to_all_llm_stages(self):
        document_client = RecordingClient(
            {
                "summary": "Summary",
                "topics": [],
                "formulas": [],
                "question_patterns": [],
                "errors": [],
            }
        )
        analyze_document(
            "TEXTBOOK",
            "PDF",
            "Course content",
            llm_client=document_client,
            language="en",
        )

        course_client = RecordingClient(
            {
                "knowledge_map": {},
                "chapter_relations": [],
                "priority_ranking": [],
                "formula_inventory": [],
                "exam_focus": [],
            }
        )
        analyze_course_documents(
            [{"document_type": "TEXTBOOK", "summary": "Summary"}],
            llm_client=course_client,
            language="en",
        )

        package_client = RecordingClient({})
        generate_learning_package({}, llm_client=package_client, language="en")

        self.assertEqual(document_client.user_prompts[0]["language"], "en")
        self.assertEqual(course_client.user_prompts[0]["language"], "en")
        self.assertEqual(package_client.user_prompts[0]["language"], "en")

    def test_existing_package_json_is_not_mutated_by_translation(self):
        package = {"course_map": {"topic": ["existing content"]}}
        original = json.loads(json.dumps(package))
        t("course_map", "en")
        self.assertEqual(package, original)


if __name__ == "__main__":
    unittest.main()

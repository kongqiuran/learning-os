import json
import unittest

from src.ai.generators.learning_package_generator import PACKAGE_KEYS, generate_learning_package
from src.ai.prompt_manager import get_prompt


class PromptContractLLMClient:
    def generate(self, system_prompt, user_prompt, stage="unknown"):
        return {
            "course_map": {"Transform methods": ["Fourier", "Laplace"]},
            "chapter_summary": [
                {
                    "chapter": chapter,
                    "summary": "Exam-oriented teaching summary",
                    "key_concepts": ["Core concept"],
                    "important_formulas": ["Core formula"],
                    "common_question_types": ["Calculation"],
                    "learning_order": "Concept, formula, then application",
                    "common_mistakes": ["Applying a property without checking conditions"],
                }
                for chapter in ("Fourier methods", "Laplace methods")
            ],
            "key_points": ["Select and apply the correct transform property"],
            "formula_book": [
                {
                    "name": f"Formula {index}",
                    "formula": f"F_{index}(x)",
                    "meaning": "A transform relationship",
                    "usage": "Solve a common exam calculation",
                    "variables": "x is the input variable",
                    "example_application": "Apply the rule to a shifted signal",
                    "common_error": "Using the wrong condition",
                    "question_type": "Calculation",
                }
                for index in range(1, 11)
            ],
            "exam_focus": [
                {
                    "topic": topic,
                    "importance": 5,
                    "core_explanation": "How the method represents and solves signal problems",
                    "must_master": ["Time shift and frequency shift"],
                    "formulas_or_rules": ["Shift property"],
                    "question_types": ["Calculation", "Integrated problem"],
                    "common_errors": ["Confusing time shift with frequency shift"],
                    "memory_tips": "A time shift changes phase rather than spectrum magnitude",
                    "study_advice": "Complete timed property exercises",
                    "evidence": ["来源于课程资料分析"],
                }
                for topic in ("Transform properties", "Inverse transforms", "Frequency analysis")
            ],
            "questions": [
                {
                    "question": f"Exam-style question {index}",
                    "answer": "Reference answer",
                    "explanation": "Method and key steps",
                    "knowledge_point": "Transform properties",
                    "question_type": (
                        "基础理解题" if index % 7 <= 3 and index % 7 != 0 else
                        "计算题" if index % 7 <= 6 and index % 7 != 0 else "综合题"
                    ),
                    "difficulty": (
                        "基础" if index <= 3 else "计算" if index <= 6 else "综合"
                    ),
                    "common_trap": "Skipping the applicability check",
                }
                for index in range(1, 15)
            ],
            "exam_strategy": {
                "priority_order": ["Transform properties", "Inverse transforms"],
                "study_advice": "Prioritize high-frequency calculations, then integrated problems.",
            },
            "study_strategy": {
                "priority_order": ["Transform properties", "Inverse transforms"],
                "before_exam_focus": ["Complete a timed calculation set"],
                "avoid_wasting_time": ["Do not memorize derivations without applications"],
                "recommended_schedule": "Use the 7-day plan, compress priorities for 3 or 1 day.",
            },
        }


class PromptUpgradeTest(unittest.TestCase):
    def test_prompts_define_exam_oriented_output_contract(self):
        document_prompt = get_prompt("document_analyzer")
        course_prompt = get_prompt("course_analyzer")
        package_prompt = get_prompt("learning_package_generator")

        for field in ("formulas", "question_patterns", "errors"):
            self.assertIn(field, document_prompt)
        for field in (
            "importance",
            "core_explanation",
            "must_master",
            "question_types",
            "common_errors",
            "memory_tips",
        ):
            self.assertIn(field, course_prompt)
            self.assertIn(field, package_prompt)
        self.assertIn("总计至少 7 题", package_prompt)
        self.assertIn("exam_strategy", package_prompt)
        self.assertIn("study_strategy", package_prompt)
        for field in ("meaning", "example_application", "common_error", "question_type"):
            self.assertIn(field, package_prompt)

    def test_learning_package_schema_and_volume_are_stable(self):
        package = generate_learning_package(
            {"exam_focus": [{"topic": "Transform properties"}]},
            llm_client=PromptContractLLMClient(),
        )

        self.assertEqual(tuple(package), PACKAGE_KEYS)
        self.assertGreaterEqual(len(package["formula_book"]), 10)
        self.assertGreaterEqual(len(package["exam_focus"]), 3)
        self.assertGreaterEqual(len(package["questions"]), 14)
        focus = package["exam_focus"][0]
        for field in (
            "importance",
            "core_explanation",
            "must_master",
            "question_types",
            "common_errors",
            "memory_tips",
        ):
            self.assertIn(field, focus)
        for chapter in package["chapter_summary"]:
            for field in (
                "summary",
                "key_concepts",
                "important_formulas",
                "common_question_types",
                "learning_order",
                "common_mistakes",
            ):
                self.assertIn(field, chapter)
        for question in package["questions"]:
            self.assertIn("question_type", question)
            self.assertIn("common_trap", question)
        self.assertIn("priority_order", package["exam_strategy"])
        self.assertIn("recommended_schedule", package["study_strategy"])
        self.assertEqual(json.loads(json.dumps(package, ensure_ascii=False)), package)


if __name__ == "__main__":
    unittest.main()

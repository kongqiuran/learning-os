import json
import unittest

from src.ai.generators.learning_package_generator import PACKAGE_KEYS, generate_learning_package
from src.ai.prompt_manager import get_prompt


class PromptContractLLMClient:
    def generate(self, system_prompt, user_prompt):
        return {
            "course_map": {"Transform methods": ["Fourier", "Laplace"]},
            "chapter_summary": [{"chapter": "Transform methods", "exam_value": "high"}],
            "key_points": ["Select and apply the correct transform property"],
            "formula_book": [
                {
                    "name": f"Formula {index}",
                    "formula": f"F_{index}(x)",
                    "usage": "Solve a common exam calculation",
                    "variables": "x is the input variable",
                    "common_error": "Using the wrong condition",
                    "question_type": "Calculation",
                }
                for index in range(1, 7)
            ],
            "exam_focus": [
                {
                    "topic": "Transform properties",
                    "importance": 5,
                    "must_master": ["Time shift and frequency shift"],
                    "must_skills": ["Apply properties to compute transforms"],
                    "question_types": ["Calculation", "Integrated problem"],
                    "common_errors": ["Confusing time shift with frequency shift"],
                    "study_advice": "Complete timed property exercises",
                    "evidence": ["来源于课程资料分析"],
                }
            ],
            "questions": [
                {
                    "question": f"Exam-style question {index}",
                    "answer": "Reference answer",
                    "explanation": "Method and key steps",
                    "knowledge_point": "Transform properties",
                    "difficulty": (
                        "基础" if index <= 3 else "计算" if index <= 6 else "综合"
                    ),
                }
                for index in range(1, 8)
            ],
            "exam_strategy": {
                "priority_order": ["Transform properties", "Inverse transforms"],
                "study_advice": "Prioritize high-frequency calculations, then integrated problems.",
            },
        }


class PromptUpgradeTest(unittest.TestCase):
    def test_prompts_define_exam_oriented_output_contract(self):
        document_prompt = get_prompt("document_analyzer")
        course_prompt = get_prompt("course_analyzer")
        package_prompt = get_prompt("learning_package_generator")

        for field in ("formulas", "question_patterns", "errors"):
            self.assertIn(field, document_prompt)
        for field in ("importance", "must_master", "question_types", "common_errors"):
            self.assertIn(field, course_prompt)
            self.assertIn(field, package_prompt)
        self.assertIn("至少生成 7 题", package_prompt)
        self.assertIn("exam_strategy", package_prompt)

    def test_learning_package_schema_and_volume_are_stable(self):
        package = generate_learning_package(
            {"exam_focus": [{"topic": "Transform properties"}]},
            llm_client=PromptContractLLMClient(),
        )

        self.assertEqual(tuple(package), PACKAGE_KEYS)
        self.assertGreaterEqual(len(package["formula_book"]), 6)
        self.assertGreaterEqual(len(package["questions"]), 7)
        focus = package["exam_focus"][0]
        for field in ("importance", "must_master", "question_types", "common_errors"):
            self.assertIn(field, focus)
        self.assertIn("priority_order", package["exam_strategy"])
        self.assertEqual(json.loads(json.dumps(package, ensure_ascii=False)), package)


if __name__ == "__main__":
    unittest.main()

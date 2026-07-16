import unittest

from src.ai.prompt_manager import STRUCTURED_OUTPUT_RULES, get_prompt
from src.api.adapters.assistant_adapter import _system_prompt


class StructuredOutputPromptTest(unittest.TestCase):
    def test_all_generation_prompts_include_strict_json_rules(self):
        for prompt_name in (
            "document_analyzer",
            "course_analyzer",
            "learning_package_generator",
        ):
            with self.subTest(prompt_name=prompt_name):
                prompt = get_prompt(prompt_name)
                self.assertIn(STRUCTURED_OUTPUT_RULES, prompt)
                self.assertIn("return ONLY valid JSON", prompt)
                self.assertIn("Python json.loads()", prompt)

    def test_course_assistant_uses_the_same_json_rules(self):
        self.assertIn(STRUCTURED_OUTPUT_RULES, _system_prompt())


if __name__ == "__main__":
    unittest.main()

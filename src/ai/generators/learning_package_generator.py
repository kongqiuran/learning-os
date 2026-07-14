import json

from src.ai.llm_client import LLMClient
from src.ai.prompt_manager import get_prompt


PACKAGE_KEYS = (
    "course_map",
    "chapter_summary",
    "key_points",
    "formula_book",
    "exam_focus",
    "questions",
)


def generate_learning_package(course_analysis, llm_client=None):
    client = llm_client or LLMClient()
    result = client.generate(
        get_prompt("learning_package_generator"),
        json.dumps(course_analysis, ensure_ascii=False),
    )
    defaults = {"course_map": {}}
    defaults.update({key: [] for key in PACKAGE_KEYS if key != "course_map"})
    return {key: result.get(key, defaults[key]) for key in PACKAGE_KEYS}

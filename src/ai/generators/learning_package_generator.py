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
    "exam_strategy",
)


def generate_learning_package(course_analysis, llm_client=None, language="zh"):
    client = llm_client or LLMClient()
    result = client.generate(
        get_prompt("learning_package_generator"),
        json.dumps(
            {"course_analysis": course_analysis, "language": language},
            ensure_ascii=False,
        ),
    )
    defaults = {"course_map": {}, "exam_strategy": {}}
    defaults.update({key: [] for key in PACKAGE_KEYS if key not in defaults})
    package = {key: result.get(key, defaults[key]) for key in PACKAGE_KEYS}
    package["exam_focus"] = [_normalize_exam_focus(item) for item in package["exam_focus"]]
    return package


def _normalize_exam_focus(item):
    if isinstance(item, str):
        item = {"topic": item}
    normalized = dict(item)
    normalized.setdefault("topic", "")
    normalized.setdefault("importance", 3)
    normalized.setdefault("must_master", [])
    normalized.setdefault("must_skills", [])
    normalized.setdefault("question_types", [])
    normalized.setdefault("common_errors", [])
    normalized.setdefault("study_advice", "根据重要程度安排复习并通过典型题自测。")
    evidence = normalized.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        normalized["evidence"] = ["来源于课程资料分析"]
    return normalized

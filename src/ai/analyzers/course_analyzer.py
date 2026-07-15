import json

from src.ai.llm_client import LLMClient
from src.ai.prompt_manager import get_prompt


DOCUMENT_TYPE_WEIGHTS = {
    "EXAM": 1.5,
    "SLIDES": 1.3,
    "HOMEWORK": 1.2,
    "TEXTBOOK": 1.0,
    "NOTES": 0.8,
    "OTHER": 0.5,
}


def analyze_course_documents(document_analyses, llm_client=None, language="zh"):
    if not document_analyses:
        raise ValueError("No document analyses are available.")
    weighted = []
    for analysis in document_analyses:
        item = dict(analysis)
        item["weight"] = DOCUMENT_TYPE_WEIGHTS.get(item.get("document_type", "OTHER"), 0.5)
        weighted.append(item)
    client = llm_client or LLMClient()
    return client.generate(
        get_prompt("course_analyzer"),
        json.dumps({"documents": weighted, "language": language}, ensure_ascii=False),
    )

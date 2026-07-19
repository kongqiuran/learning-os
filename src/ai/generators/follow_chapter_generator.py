import json

from src.ai.llm_client import LLMClient
from src.ai.prompt_manager import get_prompt


def generate_follow_chapter_package(document_analyses, llm_client=None, language="zh"):
    client = llm_client or LLMClient()
    result = client.generate(
        get_prompt("follow_chapter_generator"),
        json.dumps(
            {"documents": document_analyses, "language": language},
            ensure_ascii=False,
        ),
        stage="follow_chapter_generator",
    )
    return {
        "chapter_summary": result.get("chapter_summary", {}),
        "key_points": result.get("key_points", []),
    }

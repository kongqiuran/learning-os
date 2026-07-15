import json

from src.ai.llm_client import LLMClient
from src.ai.prompt_manager import get_prompt


def analyze_document(document_type, source_type, document_text, llm_client=None, language="zh"):
    if not document_text.strip():
        raise ValueError("Document text is empty.")
    client = llm_client or LLMClient()
    result = client.generate(
        get_prompt("document_analyzer"),
        json.dumps(
            {
                "document_type": document_type,
                "source_type": source_type,
                "document_text": document_text,
                "language": language,
            },
            ensure_ascii=False,
        ),
    )
    topics = list(result.get("topics", []))
    importance_map = {
        item.get("name", ""): item.get("importance", 1)
        for item in topics
        if isinstance(item, dict) and item.get("name")
    }
    return {
        "document_type": document_type,
        "source_type": source_type,
        "summary": str(result.get("summary", "")),
        "topics": topics,
        "formulas": list(result.get("formulas", [])),
        "question_patterns": list(result.get("question_patterns", [])),
        "errors": list(result.get("errors", [])),
        "importance_map": importance_map or dict(result.get("importance_map", {})),
        "document_metadata": {
            "document_type": document_type,
            "source_type": source_type,
        },
    }

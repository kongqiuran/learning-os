import json

from src.ai.llm_client import LLMClient
from src.ai.prompt_manager import get_prompt


def analyze_document(
    document_type,
    source_type,
    document_text=None,
    llm_client=None,
    language="zh",
    document_understanding=None,
):
    if document_understanding is None and not str(document_text or "").strip():
        raise ValueError("Document text is empty.")
    if document_understanding is not None and not document_understanding.get("pages"):
        raise ValueError("Document understanding contains no pages.")
    client = llm_client or LLMClient()
    request_payload = {
        "document_type": document_type,
        "source_type": source_type,
        "language": language,
    }
    if document_understanding is None:
        request_payload["document_text"] = document_text
    else:
        request_payload["document_understanding"] = document_understanding
    result = client.generate(
        get_prompt("document_analyzer"),
        json.dumps(request_payload, ensure_ascii=False),
        stage="document_analyzer",
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

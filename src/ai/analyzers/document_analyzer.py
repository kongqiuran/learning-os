import json

from src.ai.llm_client import LLMClient
from src.ai.prompt_manager import get_prompt


def analyze_document(document_type, source_type, document_text, llm_client=None):
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
            },
            ensure_ascii=False,
        ),
    )
    return {
        "document_type": document_type,
        "source_type": source_type,
        "summary": str(result.get("summary", "")),
        "topics": list(result.get("topics", [])),
        "importance_map": dict(result.get("importance_map", {})),
        "document_metadata": {
            "document_type": document_type,
            "source_type": source_type,
        },
    }

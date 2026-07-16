import json
from dataclasses import dataclass

from sqlalchemy import select

from src.ai.llm_client import LLMClient
from src.ai.prompt_manager import STRUCTURED_OUTPUT_RULES
from src.config import get_assistant_max_context_chars
from src.database import get_db_session
from src.models import Document, DocumentAnalysis
from src.services.analysis_service import get_learning_package


INSUFFICIENT_CONTEXT_ANSWER = "当前课程资料中没有足够信息。"
SECTION_LABELS = {
    "课程地图": "course_map",
    "章节总结": "chapter_summary",
    "重点内容": "key_points",
    "公式": "formula_book",
    "考试重点": "exam_focus",
    "练习问题": "questions",
    "学习策略": "study_strategy",
    "考试策略": "exam_strategy",
}


@dataclass(frozen=True)
class AssistantAnswer:
    answer: str
    source_files: list[str]


def answer_course_question(course_id, user_id, question, current_section=None, llm_client=None):
    context, source_files = _build_context(course_id, user_id, current_section)
    if not context:
        return AssistantAnswer(INSUFFICIENT_CONTEXT_ANSWER, [])

    client = llm_client or LLMClient()
    result = client.generate(
        _system_prompt(),
        json.dumps(
            {
                "question": question.strip(),
                "current_section": current_section,
                "course_context": context,
            },
            ensure_ascii=False,
        ),
        stage="course_assistant",
    )
    answer = str(result.get("answer", "")).strip()
    if not answer:
        answer = INSUFFICIENT_CONTEXT_ANSWER
    return AssistantAnswer(answer, source_files)


def _build_context(course_id, user_id, current_section):
    limit = get_assistant_max_context_chars()
    parts = []
    source_files = []
    remaining = limit

    package = get_learning_package(course_id, user_id)
    if package is not None and package.status == "completed" and package.content_json:
        for label, content in _ordered_package_sections(package.content_json, current_section):
            remaining = _append_bounded(parts, f"## {label}\n{_to_text(content)}", remaining)
            if remaining <= 0:
                break

    if remaining > 0:
        for document, analysis in _load_document_analyses(course_id, user_id):
            analysis_text = _to_text(
                {
                    "summary": analysis.summary,
                    "topics": analysis.topics,
                    "importance_map": analysis.importance_map,
                }
            )
            before = remaining
            remaining = _append_bounded(
                parts,
                f"## 资料分析：{document.original_filename}\n{analysis_text}",
                remaining,
            )
            if remaining < before:
                source_files.append(document.original_filename)
            if remaining <= 0:
                break

    return "\n\n".join(parts), source_files


def _ordered_package_sections(content, current_section):
    items = list(content.items())
    if not current_section:
        return items
    requested_key = SECTION_LABELS.get(current_section, current_section)
    return sorted(items, key=lambda item: item[0] != requested_key)


def _load_document_analyses(course_id, user_id):
    with get_db_session() as session:
        statement = (
            select(Document, DocumentAnalysis)
            .join(DocumentAnalysis, DocumentAnalysis.document_id == Document.id)
            .where(
                Document.course_id == int(course_id),
                Document.user_id == int(user_id),
            )
            .order_by(DocumentAnalysis.created_at.desc(), DocumentAnalysis.id.desc())
        )
        return list(session.execute(statement).all())


def _append_bounded(parts, text, remaining):
    normalized = text.strip()
    if not normalized or remaining <= 0:
        return remaining
    separator_size = 2 if parts else 0
    available = max(0, remaining - separator_size)
    if available <= 0:
        return 0
    parts.append(normalized[:available])
    return remaining - separator_size - min(len(normalized), available)


def _to_text(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def _system_prompt():
    prompt = (
        "You are the course assistant inside Learning OS. Answer only from the supplied "
        "course context. Do not use outside knowledge or invent facts. If the context does "
        f"not support an answer, return exactly {{\"answer\": \"{INSUFFICIENT_CONTEXT_ANSWER}\"}}. "
        "Otherwise return a JSON object with one concise Chinese field named answer. Explain "
        "the concept for a university student and distinguish facts from interpretation."
    )
    return f"{prompt}\n\n{STRUCTURED_OUTPUT_RULES}"

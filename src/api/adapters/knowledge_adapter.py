# 文件说明：知识点派生适配器。知识点没有独立表，这里把 DocumentAnalysis.topics 展开成前端可用的 KnowledgeItem。
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select

from src.database import get_db_session
from src.models import Course, Document, DocumentAnalysis, KnowledgeView
from src.models.user import utc_now


# re.compile 来自 Python 标准库 re，用来把字符串规则编译成正则表达式。
# knowledge_id 形如 analysis-12-topic-0，正则会解析出 analysis_id=12、topic_index=0。
# Current keys omit a version because DocumentAnalysis is immutable in the MVP.
# The optional version segment is reserved for a future analysis_version rollout.
KNOWLEDGE_KEY_PATTERN = re.compile(
    r"^analysis-(?P<analysis_id>\d+)(?:-version-(?P<analysis_version>\d+))?-topic-(?P<topic_index>\d+)$"
)


@dataclass(frozen=True)
class ParsedKnowledgeKey:
    # dataclass 来自 Python 标准库，适合表示“小数据对象”。
    # frozen=True 表示解析后的 key 不允许被修改，避免后面误改导致查错知识点。
    analysis_id: int
    topic_index: int
    analysis_version: int | None = None


@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    title: str
    content: str
    importance: int | None
    course_id: int
    course_name: str
    document_id: int
    source_file: str
    updated_at: datetime
    viewed: bool
    viewed_at: datetime | None
    core_explanation: str
    exam_value: str
    must_master: list[Any]
    memory_tips: str
    reason: str
    source_formulas: list[Any]
    source_errors: list[Any]


def list_course_knowledge(course, user_id):
    # 列出课程知识点：不是查 knowledge 表，而是查这门课下所有 DocumentAnalysis，
    # 再把每条 analysis.topics 逐个展开成 KnowledgeItem。
    with get_db_session() as session:
        statement = (
            select(Document, DocumentAnalysis)
            .join(DocumentAnalysis, DocumentAnalysis.document_id == Document.id)
            .where(
                Document.course_id == int(course.id),
                Document.user_id == int(user_id),
            )
            .order_by(Document.uploaded_at.desc(), Document.id.desc())
        )
        analyses = list(session.execute(statement).all())
        viewed_rows = list(
            session.execute(
                select(KnowledgeView.knowledge_key, KnowledgeView.viewed_at).where(
                    KnowledgeView.user_id == int(user_id)
                )
            ).all()
        )

    viewed_by_key = {key: viewed_at for key, viewed_at in viewed_rows}
    items = []
    for document, analysis in analyses:
        for topic_index, topic in enumerate(_as_list(analysis.topics)):
            item = _map_topic(
                course,
                document,
                analysis,
                topic,
                topic_index,
                viewed_by_key,
            )
            if item is not None:
                items.append(item)
    return items


def get_knowledge_item(knowledge_key, user_id):
    # 详情页传入的 knowledge_key 是派生 ID，必须先 parse 成 analysis_id + topic_index。
    # 如果格式不对或 topic_index 越界，就返回 None，让路由层返回 404。
    parsed_key = parse_knowledge_key(knowledge_key)
    if parsed_key is None or parsed_key.analysis_version is not None:
        return None

    with get_db_session() as session:
        statement = (
            select(Course, Document, DocumentAnalysis)
            .join(Document, Document.course_id == Course.id)
            .join(DocumentAnalysis, DocumentAnalysis.document_id == Document.id)
            .where(
                DocumentAnalysis.id == parsed_key.analysis_id,
                Course.user_id == int(user_id),
                Document.user_id == int(user_id),
            )
        )
        row = session.execute(statement).one_or_none()
        view = session.scalar(
            select(KnowledgeView).where(
                KnowledgeView.user_id == int(user_id),
                KnowledgeView.knowledge_key == knowledge_key,
            )
        )

    if row is None:
        return None
    course, document, analysis = row
    topics = _as_list(analysis.topics)
    if parsed_key.topic_index >= len(topics):
        return None
    viewed_by_key = {knowledge_key: view.viewed_at} if view is not None else {}
    return _map_topic(
        course,
        document,
        analysis,
        topics[parsed_key.topic_index],
        parsed_key.topic_index,
        viewed_by_key,
    )


def mark_knowledge_viewed(knowledge_key, user_id):
    # 已读状态单独写 KnowledgeView，因为知识点是从 DocumentAnalysis 派生的，不能直接在 topics 数组里写用户状态。
    item = get_knowledge_item(knowledge_key, user_id)
    if item is None:
        return None

    viewed_at = utc_now()
    with get_db_session() as session:
        view = session.scalar(
            select(KnowledgeView).where(
                KnowledgeView.user_id == int(user_id),
                KnowledgeView.knowledge_key == knowledge_key,
            )
        )
        if view is None:
            view = KnowledgeView(
                user_id=int(user_id),
                knowledge_key=knowledge_key,
                viewed_at=viewed_at,
            )
            session.add(view)
        else:
            view.viewed_at = viewed_at
        session.flush()
    return viewed_at


def create_knowledge_key(analysis_id, topic_index):
    # f"...{变量}..." 是 Python f-string 写法，用来把分析 ID 和主题序号拼成稳定的前端 ID。
    return f"analysis-{int(analysis_id)}-topic-{int(topic_index)}"


def parse_knowledge_key(knowledge_key):
    # fullmatch 来自 Python 正则对象，要求整个字符串都符合规则；这比只匹配开头更安全。
    match = KNOWLEDGE_KEY_PATTERN.fullmatch(str(knowledge_key))
    if match is None:
        return None
    version = match.group("analysis_version")
    return ParsedKnowledgeKey(
        analysis_id=int(match.group("analysis_id")),
        topic_index=int(match.group("topic_index")),
        analysis_version=int(version) if version is not None else None,
    )


def _map_topic(course, document, analysis, topic, topic_index, viewed_by_key):
    # topic 可能是 LLM 返回的 dict，也可能是简单字符串；这里统一整理成 dict，方便后面取 name/importance 等字段。
    topic_data = dict(topic) if isinstance(topic, dict) else {"name": str(topic)}
    title = str(topic_data.get("name", "")).strip()
    if not title:
        return None

    core_explanation = _as_text(topic_data.get("core_explanation"))
    exam_value = _as_text(topic_data.get("exam_value"))
    reason = _as_text(topic_data.get("reason"))
    summary = _as_text(analysis.summary)
    content = core_explanation or exam_value or reason or summary[:800]
    importance = _normalize_importance(
        topic_data.get("importance", (analysis.importance_map or {}).get(title))
    )
    knowledge_key = create_knowledge_key(analysis.id, topic_index)
    viewed_at = viewed_by_key.get(knowledge_key)
    analysis_json = analysis.analysis_json if isinstance(analysis.analysis_json, dict) else {}

    return KnowledgeItem(
        id=knowledge_key,
        title=title,
        content=content,
        importance=importance,
        course_id=course.id,
        course_name=course.name,
        document_id=document.id,
        source_file=document.original_filename,
        updated_at=analysis.created_at,
        viewed=viewed_at is not None,
        viewed_at=viewed_at,
        core_explanation=core_explanation,
        exam_value=exam_value,
        must_master=_as_list(topic_data.get("must_master")),
        memory_tips=_as_text(topic_data.get("memory_tips")),
        reason=reason,
        source_formulas=_as_list(analysis_json.get("formulas")),
        source_errors=_as_list(analysis_json.get("errors")),
    )


def _normalize_importance(value):
    if isinstance(value, bool):
        return None
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return None
    return normalized if 1 <= normalized <= 5 else None


def _as_list(value):
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def _as_text(value):
    return str(value).strip() if value is not None else ""

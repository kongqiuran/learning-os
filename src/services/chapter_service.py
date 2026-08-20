# 文件说明：章节业务服务。select/func 来自 SQLAlchemy；这里负责章节增删改查，以及把资料移动到章节或未分章节。
from sqlalchemy import func, select

from src.database import get_db_session
from src.models import Chapter, Course, Document
from src.storage import delete_document_derivatives, delete_document_file


def list_chapters(course_id, user_id):
    # list_chapters 只返回当前用户当前课程的章节。
    # join(Course) 是 SQLAlchemy 查询写法，用 Course.user_id 再做一次所有权校验。
    with get_db_session() as session:
        return list(session.scalars(select(Chapter).join(Course).where(Chapter.course_id == int(course_id), Course.user_id == int(user_id)).order_by(Chapter.position, Chapter.id)))


def create_chapter(course_id, user_id, title):
    # strip 是 Python 字符串方法，用来去掉前后空格；空标题不能创建章节。
    normalized = str(title).strip()
    if not normalized:
        raise ValueError("Chapter title is required.")
    with get_db_session() as session:
        course = session.scalar(select(Course).where(Course.id == int(course_id), Course.user_id == int(user_id)))
        if course is None:
            return None
        position = session.scalar(select(func.coalesce(func.max(Chapter.position), -1)).where(Chapter.course_id == course.id)) + 1
        chapter = Chapter(course_id=course.id, title=normalized, position=position)
        session.add(chapter)
        session.flush()
        return chapter


def update_chapter(chapter_id, course_id, user_id, title=None, position=None):
    # 更新章节时同样通过 _get 校验 chapter_id + course_id + user_id，防止用户改到别人的章节。
    with get_db_session() as session:
        chapter = _get(session, chapter_id, course_id, user_id)
        if chapter is None:
            return None
        if title is not None:
            normalized = title.strip()
            if not normalized:
                raise ValueError("Chapter title is required.")
            chapter.title = normalized
        if position is not None:
            chapter.position = int(position)
        session.flush()
        return chapter


def move_document(document_id, course_id, user_id, chapter_id):
    # 移动资料只更新 Document.chapter_id。
    # 按文档链路，这不会触发重解析；但 source_fingerprint 会让旧学习包在展示时标记为 is_stale。
    with get_db_session() as session:
        document = session.scalar(select(Document).join(Course).where(Document.id == int(document_id), Document.course_id == int(course_id), Document.user_id == int(user_id), Course.user_id == int(user_id)))
        if document is None:
            return None
        if chapter_id is not None and _get(session, chapter_id, course_id, user_id) is None:
            raise ValueError("The chapter does not exist.")
        document.chapter_id = chapter_id
        session.flush()
        return document


def delete_chapter(chapter_id, course_id, user_id, material_action):
    if material_action not in {"keep_unassigned", "delete"}:
        raise ValueError("material_action must be keep_unassigned or delete.")
    deleted_documents = []
    with get_db_session() as session:
        chapter = _get(session, chapter_id, course_id, user_id)
        if chapter is None:
            return False
        documents = list(session.scalars(select(Document).where(Document.chapter_id == chapter.id, Document.user_id == int(user_id))))
        if material_action == "keep_unassigned":
            for document in documents:
                document.chapter_id = None
        else:
            deleted_documents = [
                (document.id, document.file_path) for document in documents
            ]
            for document in documents:
                session.delete(document)
        session.delete(chapter)
    for document_id, path in deleted_documents:
        delete_document_file(path)
        delete_document_derivatives(user_id, course_id, document_id)
    return True


def _get(session, chapter_id, course_id, user_id):
    return session.scalar(select(Chapter).join(Course).where(Chapter.id == int(chapter_id), Chapter.course_id == int(course_id), Course.user_id == int(user_id)))

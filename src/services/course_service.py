from sqlalchemy import delete, select

from src.database import get_db_session
from src.models import Course, Document
from src.storage import delete_document_file


def create_course(user_id, name, description=None):
    if user_id is None:
        raise ValueError("User ID is required.")

    normalized_name = name.strip() if isinstance(name, str) else ""
    if not normalized_name:
        raise ValueError("Course name is required.")

    normalized_description = description.strip() if isinstance(description, str) else ""
    course = Course(
        user_id=int(user_id),
        name=normalized_name,
        description=normalized_description or None,
    )

    with get_db_session() as session:
        session.add(course)
        session.flush()

    return course


def list_courses_for_user(user_id):
    if user_id is None:
        return []

    with get_db_session() as session:
        statement = (
            select(Course)
            .where(Course.user_id == int(user_id))
            .order_by(Course.created_at.desc(), Course.id.desc())
        )
        return list(session.scalars(statement))


def get_course_for_user(course_id, user_id):
    if course_id is None or user_id is None:
        return None

    with get_db_session() as session:
        statement = select(Course).where(
            Course.id == int(course_id),
            Course.user_id == int(user_id),
        )
        return session.scalar(statement)


def delete_course_for_user(course_id, user_id):
    if course_id is None or user_id is None:
        return False

    with get_db_session() as session:
        file_paths = list(
            session.scalars(
                select(Document.file_path).where(
                    Document.course_id == int(course_id),
                    Document.user_id == int(user_id),
                )
            )
        )
        statement = delete(Course).where(
            Course.id == int(course_id),
            Course.user_id == int(user_id),
        )
        result = session.execute(statement)

    if result.rowcount > 0:
        for file_path in file_paths:
            delete_document_file(file_path)
        return True
    return False

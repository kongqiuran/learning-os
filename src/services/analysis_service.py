from datetime import datetime, timezone
from sqlalchemy import func, select

from src.ai.analyzers.course_analyzer import analyze_course_documents
from src.ai.analyzers.document_analyzer import analyze_document
from src.ai.generators.learning_package_generator import generate_learning_package
from src.ai.llm_client import LLMClient
from src.config import get_max_chars_per_request
from src.database import get_db_session
from src.models import Course, Document, DocumentAnalysis, LearningPackage
from src.services.file_parser_service import extract_text, get_source_type


class TenantIsolationError(ValueError):
    """Raised when a background task's resource ownership tuple is invalid."""


SCENE_TYPES = {
    "follow": {"SLIDES", "HOMEWORK", "OTHER", "NOTES"},
    "textbook": {"TEXTBOOK"},
    "exam": {"EXAM", "HOMEWORK"},
}


def analyze_course(course_id, user_id, llm_client=None, language="zh", package_id=None, scene=None, scope_document_id=None):
    course, documents = _load_course_documents(course_id, user_id, scene, scope_document_id)
    if course is None:
        raise ValueError("The course does not exist or access is denied.")
    if not documents:
        raise ValueError("Upload at least one supported document before generating a learning package.")
    _validate_document_course_binding(course_id, documents)

    package = (
        _start_existing_package(package_id, course.id, user_id)
        if package_id is not None
        else _create_package(course.id, user_id, "processing")
    )
    try:
        client = llm_client or LLMClient(
            progress_callback=lambda **progress: _update_package_progress(
                package.id,
                course.id,
                user_id,
                **progress,
            )
        )
        analyses = []
        for document in documents:
            _update_package_progress(
                package.id,
                course.id,
                user_id,
                "document_analyzer",
                0,
            )
            analyses.append(
                _get_or_create_document_analysis(
                    document,
                    course.id,
                    user_id,
                    client,
                    language,
                )
            )
        _update_package_progress(package.id, course.id, user_id, "course_analyzer", 0)
        course_analysis = analyze_course_documents(
            analyses,
            llm_client=client,
            language=language,
        )
        _update_package_progress(
            package.id,
            course.id,
            user_id,
            "learning_package_generator",
            0,
        )
        content = generate_learning_package(
            course_analysis,
            llm_client=client,
            language=language,
        )
        with get_db_session() as session:
            stored_package = _require_scoped_package(
                session,
                package.id,
                course.id,
                user_id,
            )
            stored_package.status = "completed"
            stored_package.content_json = content
            stored_package.current_stage = "completed"
            stored_package.error_type = None
            stored_package.error_detail = None
            stored_package.finished_at = datetime.now(timezone.utc)
        package.status = "completed"
        package.content_json = content
        package.current_stage = "completed"
        package.error_type = None
        package.error_detail = None
        return package
    except TenantIsolationError:
        raise
    except Exception as exc:
        error_type = getattr(exc, "error_type", type(exc).__name__)
        error_detail = _format_error_detail(exc)
        with get_db_session() as session:
            stored_package = _require_scoped_package(
                session,
                package.id,
                course.id,
                user_id,
            )
            stored_package.status = "failed"
            stored_package.current_stage = getattr(
                exc,
                "stage",
                stored_package.current_stage or "unknown",
            )
            stored_package.retry_count = getattr(
                exc,
                "retry_count",
                stored_package.retry_count or 0,
            )
            stored_package.error_type = error_type
            stored_package.error_detail = error_detail
            stored_package.finished_at = datetime.now(timezone.utc)
            stored_package.content_json = {
                "error": {
                    "code": "generation_failed",
                    "message": "Course content generation failed.",
                }
            }
        raise


def get_learning_package(course_id, user_id):
    if course_id is None or user_id is None:
        return None
    with get_db_session() as session:
        return session.scalar(
            select(LearningPackage)
            .join(Course)
            .where(Course.id == int(course_id), Course.user_id == int(user_id))
            .order_by(LearningPackage.version.desc(), LearningPackage.id.desc())
        )


def get_scene_packages(course_id, user_id):
    result = {}
    with get_db_session() as session:
        for scene in SCENE_TYPES:
            result[scene] = session.scalar(select(LearningPackage).join(Course).where(LearningPackage.course_id == int(course_id), Course.user_id == int(user_id), LearningPackage.scene == scene).order_by(LearningPackage.version.desc(), LearningPackage.id.desc()))
    return result


def get_learning_package_task(package_id, course_id, user_id):
    if package_id is None or course_id is None or user_id is None:
        return None
    with get_db_session() as session:
        return session.scalar(
            select(LearningPackage)
            .join(Course)
            .where(
                LearningPackage.id == int(package_id),
                LearningPackage.course_id == int(course_id),
                Course.user_id == int(user_id),
            )
        )


def create_learning_package_task(course_id, user_id, scene="legacy", scope_document_id=None):
    course, documents = _load_course_documents(course_id, user_id, None if scene == "legacy" else scene, scope_document_id)
    if course is None:
        raise ValueError("The course does not exist or access is denied.")
    if not documents:
        raise ValueError("Upload at least one supported document before generating a learning package.")
    _validate_document_course_binding(course_id, documents)
    package = _create_package(course.id, user_id, "pending")
    with get_db_session() as session:
        stored = session.get(LearningPackage, package.id)
        stored.scene = scene
        stored.scope_document_id = scope_document_id
        session.flush()
        package.scene = scene
        package.scope_document_id = scope_document_id
    return package


def _validate_document_course_binding(course_id, documents):
    if any(document.course_id != int(course_id) for document in documents):
        raise ValueError("Document-course mismatch detected.")


def _load_course_documents(course_id, user_id, scene=None, scope_document_id=None):
    if course_id is None or user_id is None:
        return None, []
    with get_db_session() as session:
        course = session.scalar(
            select(Course).where(Course.id == int(course_id), Course.user_id == int(user_id))
        )
        statement = (
                select(Document)
                .join(Course, Document.course_id == Course.id)
                .where(
                    Document.course_id == int(course_id),
                    Document.user_id == int(user_id),
                    Course.user_id == int(user_id),
                )
                .order_by(Document.id)
        )
        if scene in SCENE_TYPES:
            statement = statement.where(Document.document_type.in_(SCENE_TYPES[scene]))
        if scope_document_id is not None:
            statement = statement.where(Document.id == int(scope_document_id))
        documents = list(session.scalars(statement))
        return course, documents


def _create_package(course_id, user_id, status):
    with get_db_session() as session:
        _require_scoped_course(session, course_id, user_id)
        latest_version = session.scalar(
            select(func.max(LearningPackage.version)).where(LearningPackage.course_id == course_id)
        )
        package = LearningPackage(
            course_id=course_id,
            status=status,
            version=(latest_version or 0) + 1,
            content_json={},
            current_stage="pending" if status == "pending" else "starting",
            retry_count=0,
        )
        session.add(package)
        session.flush()
    return package


def _start_existing_package(package_id, course_id, user_id):
    with get_db_session() as session:
        package = _require_scoped_package(session, package_id, course_id, user_id)
        if package.status not in {"pending", "processing"}:
            raise ValueError("The generation task is not active.")
        package.status = "processing"
        package.current_stage = "starting"
        package.retry_count = 0
        package.error_type = None
        package.error_detail = None
        session.flush()
    return package


def _update_package_progress(package_id, course_id, user_id, stage, retry_count):
    with get_db_session() as session:
        package = _require_scoped_package(session, package_id, course_id, user_id)
        package.current_stage = stage
        package.retry_count = int(retry_count)


def _require_scoped_course(session, course_id, user_id):
    course = session.scalar(
        select(Course).where(
            Course.id == int(course_id),
            Course.user_id == int(user_id),
        )
    )
    if course is None:
        raise TenantIsolationError(
            "Tenant isolation check failed for course "
            f"(course_id={course_id}, user_id={user_id})."
        )
    return course


def _require_scoped_package(session, package_id, course_id, user_id):
    package = session.scalar(
        select(LearningPackage)
        .join(Course, LearningPackage.course_id == Course.id)
        .where(
            LearningPackage.id == int(package_id),
            LearningPackage.course_id == int(course_id),
            Course.user_id == int(user_id),
        )
    )
    if package is None:
        raise TenantIsolationError(
            "Tenant isolation check failed for learning package "
            f"(package_id={package_id}, course_id={course_id}, user_id={user_id})."
        )
    return package


def _require_scoped_document(session, document_id, course_id, user_id):
    document = session.scalar(
        select(Document)
        .join(Course, Document.course_id == Course.id)
        .where(
            Document.id == int(document_id),
            Document.course_id == int(course_id),
            Document.user_id == int(user_id),
            Course.user_id == int(user_id),
        )
    )
    if document is None:
        raise TenantIsolationError(
            "Tenant isolation check failed for document "
            f"(document_id={document_id}, course_id={course_id}, user_id={user_id})."
        )
    return document


def _format_error_detail(exc):
    detail = str(exc).strip() or type(exc).__name__
    preview = getattr(exc, "response_preview", None)
    if preview:
        detail = f"{detail} Response preview: {preview}"
    return detail[:4000]


def _get_or_create_document_analysis(
    document,
    course_id,
    user_id,
    llm_client,
    language="zh",
):
    with get_db_session() as session:
        stored_document = _require_scoped_document(
            session,
            document.id,
            course_id,
            user_id,
        )
        existing = session.scalar(
            select(DocumentAnalysis).where(DocumentAnalysis.document_id == document.id)
        )
        if existing is not None:
            return _serialize_analysis(stored_document, existing)

    try:
        text = extract_text(document.file_path, document.mime_type)
        source_type = get_source_type(document.file_path, document.mime_type)
        result = analyze_document(
            document.document_type,
            source_type,
            text[: get_max_chars_per_request()],
            llm_client=llm_client,
            language=language,
        )
        analysis = DocumentAnalysis(
            document_id=document.id,
            summary=result["summary"],
            topics=result["topics"],
            importance_map=result["importance_map"],
            analysis_json=result,
        )
        with get_db_session() as session:
            stored_document = _require_scoped_document(
                session,
                document.id,
                course_id,
                user_id,
            )
            session.add(analysis)
            stored_document.processing_status = "completed"
            session.flush()
        return _serialize_analysis(document, analysis)
    except TenantIsolationError:
        raise
    except Exception:
        with get_db_session() as session:
            stored_document = _require_scoped_document(
                session,
                document.id,
                course_id,
                user_id,
            )
            stored_document.processing_status = "failed"
        raise


def _serialize_analysis(document, analysis):
    source_type = get_source_type(document.file_path, document.mime_type)
    serialized = dict(analysis.analysis_json or {})
    serialized.update({
        "document_type": document.document_type,
        "source_type": source_type,
        "summary": analysis.summary,
        "topics": analysis.topics,
        "importance_map": analysis.importance_map,
        "document_metadata": {
            "document_type": document.document_type,
            "source_type": source_type,
        },
    })
    serialized.setdefault("formulas", [])
    serialized.setdefault("question_patterns", [])
    serialized.setdefault("errors", [])
    return serialized

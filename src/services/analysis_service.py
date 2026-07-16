from sqlalchemy import func, select

from src.ai.analyzers.course_analyzer import analyze_course_documents
from src.ai.analyzers.document_analyzer import analyze_document
from src.ai.generators.learning_package_generator import generate_learning_package
from src.config import get_max_chars_per_request
from src.database import get_db_session
from src.models import Course, Document, DocumentAnalysis, LearningPackage
from src.services.file_parser_service import extract_text, get_source_type


def analyze_course(course_id, user_id, llm_client=None, language="zh", package_id=None):
    course, documents = _load_course_documents(course_id, user_id)
    if course is None:
        raise ValueError("The course does not exist or access is denied.")
    if not documents:
        raise ValueError("Upload at least one supported document before generating a learning package.")
    _validate_document_course_binding(course_id, documents)

    package = (
        _start_existing_package(package_id, course.id)
        if package_id is not None
        else _create_package(course.id, "processing")
    )
    try:
        analyses = [
            _get_or_create_document_analysis(document, llm_client, language)
            for document in documents
        ]
        course_analysis = analyze_course_documents(
            analyses,
            llm_client=llm_client,
            language=language,
        )
        content = generate_learning_package(
            course_analysis,
            llm_client=llm_client,
            language=language,
        )
        with get_db_session() as session:
            stored_package = session.get(LearningPackage, package.id)
            stored_package.status = "completed"
            stored_package.content_json = content
        package.status = "completed"
        package.content_json = content
        return package
    except Exception:
        with get_db_session() as session:
            stored_package = session.get(LearningPackage, package.id)
            if stored_package is not None:
                stored_package.status = "failed"
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


def create_learning_package_task(course_id, user_id):
    course, documents = _load_course_documents(course_id, user_id)
    if course is None:
        raise ValueError("The course does not exist or access is denied.")
    if not documents:
        raise ValueError("Upload at least one supported document before generating a learning package.")
    _validate_document_course_binding(course_id, documents)
    return _create_package(course.id, "pending")


def _validate_document_course_binding(course_id, documents):
    if any(document.course_id != int(course_id) for document in documents):
        raise ValueError("Document-course mismatch detected.")


def _load_course_documents(course_id, user_id):
    if course_id is None or user_id is None:
        return None, []
    with get_db_session() as session:
        course = session.scalar(
            select(Course).where(Course.id == int(course_id), Course.user_id == int(user_id))
        )
        documents = list(
            session.scalars(
                select(Document)
                .where(
                    Document.course_id == int(course_id),
                    Document.user_id == int(user_id),
                )
                .order_by(Document.id)
            )
        )
        return course, documents


def _create_package(course_id, status):
    with get_db_session() as session:
        latest_version = session.scalar(
            select(func.max(LearningPackage.version)).where(LearningPackage.course_id == course_id)
        )
        package = LearningPackage(
            course_id=course_id,
            status=status,
            version=(latest_version or 0) + 1,
            content_json={},
        )
        session.add(package)
        session.flush()
    return package


def _start_existing_package(package_id, course_id):
    with get_db_session() as session:
        package = session.scalar(
            select(LearningPackage).where(
                LearningPackage.id == int(package_id),
                LearningPackage.course_id == int(course_id),
            )
        )
        if package is None:
            raise ValueError("The generation task was not found.")
        if package.status not in {"pending", "processing"}:
            raise ValueError("The generation task is not active.")
        package.status = "processing"
        session.flush()
    return package


def _get_or_create_document_analysis(document, llm_client, language="zh"):
    with get_db_session() as session:
        existing = session.scalar(
            select(DocumentAnalysis).where(DocumentAnalysis.document_id == document.id)
        )
        if existing is not None:
            return _serialize_analysis(document, existing)

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
            session.add(analysis)
            stored_document = session.get(Document, document.id)
            stored_document.processing_status = "completed"
            session.flush()
        return _serialize_analysis(document, analysis)
    except Exception:
        with get_db_session() as session:
            stored_document = session.get(Document, document.id)
            if stored_document is not None:
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

from sqlalchemy import func, select

from src.ai.analyzers.course_analyzer import analyze_course_documents
from src.ai.analyzers.document_analyzer import analyze_document
from src.ai.generators.learning_package_generator import generate_learning_package
from src.config import get_max_chars_per_request
from src.database import get_db_session
from src.models import Course, Document, DocumentAnalysis, LearningPackage
from src.services.pdf_service import extract_text


def analyze_course(course_id, user_id, llm_client=None):
    course, documents = _load_course_documents(course_id, user_id)
    if course is None:
        raise ValueError("The course does not exist or access is denied.")
    if not documents:
        raise ValueError("Upload at least one PDF before generating a learning package.")

    package = _create_processing_package(course.id)
    try:
        analyses = [_get_or_create_document_analysis(document, llm_client) for document in documents]
        course_analysis = analyze_course_documents(analyses, llm_client=llm_client)
        content = generate_learning_package(course_analysis, llm_client=llm_client)
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
                    Document.mime_type == "application/pdf",
                )
                .order_by(Document.id)
            )
        )
        return course, documents


def _create_processing_package(course_id):
    with get_db_session() as session:
        latest_version = session.scalar(
            select(func.max(LearningPackage.version)).where(LearningPackage.course_id == course_id)
        )
        package = LearningPackage(
            course_id=course_id,
            status="processing",
            version=(latest_version or 0) + 1,
            content_json={},
        )
        session.add(package)
        session.flush()
    return package


def _get_or_create_document_analysis(document, llm_client):
    with get_db_session() as session:
        existing = session.scalar(
            select(DocumentAnalysis).where(DocumentAnalysis.document_id == document.id)
        )
        if existing is not None:
            return _serialize_analysis(document.document_type, existing)

    try:
        text = extract_text(document.file_path)
        result = analyze_document(
            document.document_type,
            text[: get_max_chars_per_request()],
            llm_client=llm_client,
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
        return _serialize_analysis(document.document_type, analysis)
    except Exception:
        with get_db_session() as session:
            stored_document = session.get(Document, document.id)
            if stored_document is not None:
                stored_document.processing_status = "failed"
        raise


def _serialize_analysis(document_type, analysis):
    return {
        "document_type": document_type,
        "summary": analysis.summary,
        "topics": analysis.topics,
        "importance_map": analysis.importance_map,
    }

from datetime import datetime, timezone
import hashlib
from sqlalchemy import func, select

from src.ai.analyzers.course_analyzer import analyze_course_documents
from src.ai.analyzers.document_analyzer import analyze_document
from src.ai.document.pipeline import (
    DOCUMENT_INTELLIGENCE_PIPELINE_VERSION,
    understand_pdf,
)
from src.ai.generators.follow_chapter_generator import generate_follow_chapter_package
from src.ai.generators.learning_package_generator import generate_learning_package
from src.ai.llm_client import LLMClient
from src.ai.providers.qwen_vision_provider import QwenVisionProvider
from src.config import get_max_chars_per_request, get_vision_config
from src.database import get_db_session
from src.models import Course, Document, DocumentAnalysis, LearningPackage
from src.services.file_parser_service import extract_text, get_source_type
from src.services.task_service import create_package_task, sync_package_task
from src.logging_config import get_logger


class TenantIsolationError(ValueError):
    """Raised when a background task's resource ownership tuple is invalid."""


SCENE_TYPES = {
    "follow": {"SLIDES", "HOMEWORK", "OTHER", "NOTES"},
    "textbook": {"TEXTBOOK"},
    "exam": {"EXAM", "HOMEWORK"},
}
PROMPT_VERSION = "follow-chapter-v1"
logger = get_logger(__name__)


def get_scope_metadata(scope_document_id=None, scope_chapter_id=None, scope_unassigned=False):
    if scope_document_id is not None:
        return "document", f"document:{int(scope_document_id)}"
    if scope_chapter_id is not None:
        return "chapter", f"chapter:{int(scope_chapter_id)}"
    if scope_unassigned:
        return "unassigned", "unassigned"
    return "course", "course"


def validate_generation_scope(scene, scope_document_id=None, scope_chapter_id=None, scope_unassigned=False):
    selected = sum((scope_document_id is not None, scope_chapter_id is not None, bool(scope_unassigned)))
    if selected > 1:
        raise ValueError("Choose exactly one generation scope.")
    if scene == "follow" and not (scope_chapter_id is not None or scope_unassigned):
        raise ValueError("Follow-course generation must target one chapter.")
    if scene == "textbook" and scope_document_id is None:
        raise ValueError("Textbook generation must target one textbook document.")
    if scene == "exam" and selected:
        raise ValueError("Exam generation is course-scoped and does not accept a chapter or document.")


def analyze_course(course_id, user_id, llm_client=None, language="zh", package_id=None, scene=None, scope_document_id=None, scope_chapter_id=None, scope_unassigned=False):
    course, documents = _load_course_documents(course_id, user_id, scene, scope_document_id, scope_chapter_id, scope_unassigned)
    if course is None:
        raise ValueError("The course does not exist or access is denied.")
    if not documents:
        raise ValueError("Upload at least one supported document before generating a learning package.")
    _validate_document_course_binding(course_id, documents)

    package = (
        _start_existing_package(package_id, course.id, user_id)
        if package_id is not None
        else _create_package(course.id, user_id, "processing", scene or "legacy", scope_document_id, scope_chapter_id, scope_unassigned, documents)
    )
    try:
        client = llm_client or LLMClient(
            progress_callback=lambda **progress: _update_package_progress(
                package.id,
                course.id,
                user_id,
                **progress,
            ),
            log_context={
                "user_id": user_id,
                "task_id": package.task_id,
                "document_id": None,
                "course_id": course.id,
                "package_id": package.id,
                "scene": scene or "legacy",
            },
        )
        _set_llm_log_context(
            client,
            user_id=user_id,
            task_id=package.task_id,
            document_id=None,
            course_id=course.id,
            package_id=package.id,
            scene=scene or "legacy",
        )
        analyses = []
        for document in documents:
            _set_llm_log_context(client, document_id=document.id)
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
                    package.id,
                    package.task_id,
                )
            )
        _set_llm_log_context(client, document_id=None)
        if scene == "follow" and (scope_chapter_id is not None or scope_unassigned):
            _update_package_progress(package.id, course.id, user_id, "follow_chapter_generator", 0)
            content = generate_follow_chapter_package(analyses, llm_client=client, language=language)
        else:
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
            sync_package_task(session, stored_package, user_id, status="SUCCESS", stage="completed")
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
            sync_package_task(
                session,
                stored_package,
                user_id,
                status="FAILED",
                stage=stored_package.current_stage,
                error_code=error_type,
                error_detail=error_detail,
            )
        logger.exception(
            "Course analysis failed.",
            extra={
                "event": "analysis.course.failed",
                "user_id": user_id,
                "task_id": package.task_id,
                "document_id": scope_document_id,
                "course_id": course.id,
                "package_id": package.id,
                "scene": scene or "legacy",
                "stage": getattr(exc, "stage", None),
                "exception": exc,
            },
        )
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


def get_scene_packages(course_id, user_id, completed_only=False):
    result = {}
    with get_db_session() as session:
        for scene in SCENE_TYPES:
            statement = select(LearningPackage).join(Course).where(
                LearningPackage.course_id == int(course_id),
                Course.user_id == int(user_id),
                LearningPackage.scene == scene,
                LearningPackage.scope_key == "course",
            )
            if completed_only:
                statement = statement.where(LearningPackage.status == "completed")
            package = session.scalar(statement.order_by(LearningPackage.version.desc(), LearningPackage.id.desc()))
            result[scene] = _mark_package_staleness(session, package)
    return result


def get_scoped_packages(course_id, user_id, completed_only=False):
    chapter_packages = {}
    document_packages = {}
    with get_db_session() as session:
        packages = session.scalars(
            select(LearningPackage)
            .join(Course)
            .where(
                LearningPackage.course_id == int(course_id),
                Course.user_id == int(user_id),
                LearningPackage.scene.in_(("follow", "textbook")),
                LearningPackage.scope_key != "course",
            )
            .order_by(LearningPackage.version.desc(), LearningPackage.id.desc())
        )
        for package in packages:
            if completed_only and package.status != "completed":
                continue
            _mark_package_staleness(session, package)
            if package.scene == "follow":
                if package.scope_chapter_id is not None:
                    chapter_packages.setdefault(str(package.scope_chapter_id), package)
                elif package.scope_unassigned:
                    chapter_packages.setdefault("unassigned", package)
            elif package.scene == "textbook" and package.scope_document_id is not None:
                document_packages.setdefault(str(package.scope_document_id), package)
    return chapter_packages, document_packages


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


def create_learning_package_task(course_id, user_id, scene="legacy", scope_document_id=None, scope_chapter_id=None, scope_unassigned=False, usage_record_id=None, entitlement_id=None, quota_source=None):
    if scene != "legacy":
        validate_generation_scope(scene, scope_document_id, scope_chapter_id, scope_unassigned)
    course, documents = _load_course_documents(course_id, user_id, None if scene == "legacy" else scene, scope_document_id, scope_chapter_id, scope_unassigned)
    if course is None:
        raise ValueError("The course does not exist or access is denied.")
    if not documents:
        raise ValueError("Upload at least one supported document before generating a learning package.")
    _validate_document_course_binding(course_id, documents)
    package = _create_package(course.id, user_id, "pending", scene, scope_document_id, scope_chapter_id, scope_unassigned, documents, usage_record_id, entitlement_id, quota_source)
    with get_db_session() as session:
        stored = session.get(LearningPackage, package.id)
        stored.scene = scene
        stored.scope_document_id = scope_document_id
        stored.scope_chapter_id = scope_chapter_id
        stored.scope_unassigned = bool(scope_unassigned)
        session.flush()
        package.scene = scene
        package.scope_document_id = scope_document_id
        package.scope_chapter_id = scope_chapter_id
        package.scope_unassigned = bool(scope_unassigned)
    return package


def get_active_scoped_package(course_id, user_id, scene, scope_key):
    with get_db_session() as session:
        return session.scalar(
            select(LearningPackage)
            .join(Course)
            .where(
                LearningPackage.course_id == int(course_id),
                Course.user_id == int(user_id),
                LearningPackage.scene == scene,
                LearningPackage.scope_key == scope_key,
                LearningPackage.status.in_(("pending", "processing")),
            )
            .order_by(LearningPackage.created_at.desc(), LearningPackage.id.desc())
        )


def _validate_document_course_binding(course_id, documents):
    if any(document.course_id != int(course_id) for document in documents):
        raise ValueError("Document-course mismatch detected.")


def _load_course_documents(course_id, user_id, scene=None, scope_document_id=None, scope_chapter_id=None, scope_unassigned=False):
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
        if scope_chapter_id is not None:
            statement = statement.where(Document.chapter_id == int(scope_chapter_id))
        elif scope_unassigned:
            statement = statement.where(Document.chapter_id.is_(None))
        documents = list(session.scalars(statement))
        return course, documents


def _create_package(course_id, user_id, status, scene="legacy", scope_document_id=None, scope_chapter_id=None, scope_unassigned=False, documents=None, usage_record_id=None, entitlement_id=None, quota_source=None):
    scope_kind, scope_key = get_scope_metadata(scope_document_id, scope_chapter_id, scope_unassigned)
    with get_db_session() as session:
        _require_scoped_course(session, course_id, user_id)
        latest_version = session.scalar(
            select(func.max(LearningPackage.version)).where(
                LearningPackage.course_id == course_id,
                LearningPackage.scene == scene,
                LearningPackage.scope_key == scope_key,
            )
        )
        package = LearningPackage(
            course_id=course_id,
            status=status,
            version=(latest_version or 0) + 1,
            content_json={},
            current_stage="pending" if status == "pending" else "starting",
            retry_count=0,
            scene=scene,
            scope_document_id=scope_document_id,
            scope_chapter_id=scope_chapter_id,
            scope_unassigned=bool(scope_unassigned),
            scope_kind=scope_kind,
            scope_key=scope_key,
            source_fingerprint=_source_fingerprint(documents or []),
            prompt_version=PROMPT_VERSION if scene == "follow" and scope_kind in {"chapter", "unassigned"} else None,
            usage_record_id=usage_record_id,
            entitlement_id=entitlement_id,
            quota_source=quota_source,
            quota_state="reserved" if quota_source else None,
            quota_reserved_at=datetime.now(timezone.utc) if quota_source else None,
        )
        task = create_package_task(session, user_id, course_id, scene)
        package.task = task
        package.task_id = task.id
        session.add(package)
        session.flush()
        task.resource_id = package.id
        session.flush()
    return package


def _source_fingerprint(documents):
    payload = "|".join(
        f"{item.id}:{item.document_type}:{getattr(item, 'chapter_id', None)}:{item.file_size}"
        for item in sorted(documents, key=lambda value: value.id)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _mark_package_staleness(session, package):
    if package is None:
        return None
    package.is_stale = False
    if not package.source_fingerprint:
        return package
    statement = select(Document).where(Document.course_id == package.course_id)
    if package.scene in SCENE_TYPES:
        statement = statement.where(Document.document_type.in_(SCENE_TYPES[package.scene]))
    if package.scope_kind == "document":
        statement = statement.where(Document.id == package.scope_document_id)
    elif package.scope_kind == "chapter":
        statement = statement.where(Document.chapter_id == package.scope_chapter_id)
    elif package.scope_kind == "unassigned":
        statement = statement.where(Document.chapter_id.is_(None))
    package.is_stale = _source_fingerprint(list(session.scalars(statement))) != package.source_fingerprint
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
        sync_package_task(session, package, user_id, status="RUNNING", stage="starting")
        session.flush()
    return package


def _update_package_progress(
    package_id,
    course_id,
    user_id,
    stage,
    retry_count=0,
    progress=None,
):
    with get_db_session() as session:
        package = _require_scoped_package(session, package_id, course_id, user_id)
        package.current_stage = stage
        package.retry_count = int(retry_count)
        sync_package_task(
            session,
            package,
            user_id,
            status="RUNNING",
            stage=stage,
            progress=progress,
        )


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
    package_id=None,
    task_id=None,
):
    source_type = get_source_type(document.file_path, document.mime_type)
    vision_config = get_vision_config()
    document_intelligence_enabled = (
        source_type == "PDF" and vision_config.enabled
    )
    vision_provider_available = bool(
        document_intelligence_enabled
        and QwenVisionProvider(config=vision_config).is_available()
    )
    existing_id = None
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
        existing_id = existing.id if existing is not None else None
        existing_pipeline_version = (
            (existing.analysis_json or {}).get("_pipeline_version")
            if existing is not None
            else None
        )
        should_refresh = bool(
            existing is not None
            and document_intelligence_enabled
            and vision_provider_available
            and existing_pipeline_version != DOCUMENT_INTELLIGENCE_PIPELINE_VERSION
        )
        if existing is not None and not should_refresh:
            stored_document.processing_status = "completed"
            logger.info(
                "Document analysis cache hit.",
                extra={
                    "event": "document.parse.cache_hit",
                    "user_id": user_id,
                    "task_id": task_id,
                    "document_id": document.id,
                    "course_id": course_id,
                },
            )
            return _serialize_analysis(stored_document, existing)

        stored_document.processing_status = "processing"

    try:
        started = datetime.now(timezone.utc)
        logger.info(
            "Document parsing started.",
            extra={
                "event": "document.parse.started",
                "user_id": user_id,
                "task_id": task_id,
                "document_id": document.id,
                "course_id": course_id,
            },
        )
        if document_intelligence_enabled:
            understanding = understand_pdf(
                document,
                user_id=user_id,
                course_id=course_id,
                task_id=task_id,
                progress_callback=lambda **state: _update_package_progress(
                    package_id,
                    course_id,
                    user_id,
                    state["stage"],
                    progress=state["progress"],
                ),
            )
            _update_package_progress(
                package_id,
                course_id,
                user_id,
                "knowledge_generation",
                progress=65,
            )
            result = analyze_document(
                document.document_type,
                source_type,
                llm_client=llm_client,
                language=language,
                document_understanding=understanding.to_prompt_payload(
                    get_max_chars_per_request()
                ),
            )
            required_visual_pages = any(
                page.requires_vision for page in understanding.pages
            )
            result["_pipeline_version"] = (
                DOCUMENT_INTELLIGENCE_PIPELINE_VERSION
                if understanding.vision_provider_available
                or not required_visual_pages
                else "text-v1"
            )
            result["_vision_degraded"] = understanding.degraded
        else:
            text = extract_text(document.file_path, document.mime_type)
            result = analyze_document(
                document.document_type,
                source_type,
                text[: get_max_chars_per_request()],
                llm_client=llm_client,
                language=language,
            )
            result["_pipeline_version"] = "text-v1"
        with get_db_session() as session:
            stored_document = _require_scoped_document(
                session,
                document.id,
                course_id,
                user_id,
            )
            analysis = session.scalar(
                select(DocumentAnalysis).where(
                    DocumentAnalysis.document_id == document.id
                )
            )
            if analysis is None:
                analysis = DocumentAnalysis(document_id=document.id)
                session.add(analysis)
            analysis.summary = result["summary"]
            analysis.topics = result["topics"]
            analysis.importance_map = result["importance_map"]
            analysis.analysis_json = result
            analysis.created_at = datetime.now(timezone.utc)
            stored_document.processing_status = "completed"
            session.flush()
        logger.info(
            "Document parsing and analysis completed.",
            extra={
                "event": "document.parse.success",
                "user_id": user_id,
                "task_id": task_id,
                "document_id": document.id,
                "course_id": course_id,
                "duration_ms": int((datetime.now(timezone.utc) - started).total_seconds() * 1000),
            },
        )
        return _serialize_analysis(document, analysis)
    except TenantIsolationError:
        raise
    except Exception as exc:
        with get_db_session() as session:
            stored_document = _require_scoped_document(
                session,
                document.id,
                course_id,
                user_id,
            )
            stored_document.processing_status = (
                "completed" if existing_id is not None else "failed"
            )
        logger.exception(
            "Document parsing or analysis failed.",
            extra={
                "event": "document.parse.failed",
                "user_id": user_id,
                "task_id": task_id,
                "document_id": document.id,
                "course_id": course_id,
                "exception": exc,
            },
        )
        raise


def _set_llm_log_context(client, **context):
    setter = getattr(client, "set_log_context", None)
    if callable(setter):
        setter(**context)


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

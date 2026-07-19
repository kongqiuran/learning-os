import logging
import os

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status

from src.api.adapters.assistant_adapter import answer_course_question
from src.api.adapters.generation_adapter import (
    GenerationInProgressError,
    queue_course_package,
    run_queued_course_package,
)
from src.api.adapters.upload_adapter import ServiceUploadFile
from src.api.dependencies import require_current_user
from src.api.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    CourseSpaceResponse,
    DocumentResponse,
    LearningPackageResponse,
    MessageResponse,
)
from src.api.serializers import (
    serialize_course_space,
    serialize_document,
    serialize_learning_package,
)
from src.services.analysis_service import get_learning_package, get_learning_package_task, get_scene_packages
from src.services.chapter_service import list_chapters
from src.services.course_service import get_course_for_user
from src.services.document_service import (
    DocumentUploadError,
    delete_document_for_user,
    list_documents_for_course,
    save_uploaded_document,
)
from src.services.quota_service import (
    UsageQuotaExceededError,
    release_ai_generation,
    reserve_ai_generation,
)
from src.services.entitlement_service import EntitlementQuotaExceeded, consume_assistant, get_active_entitlement, require_scene_allowance


router = APIRouter(prefix="/api/courses/{course_id}", tags=["course-space"])
logger = logging.getLogger(__name__)


@router.get("/space", response_model=CourseSpaceResponse)
def get_course_space(course_id: int, user=Depends(require_current_user)):
    course = _require_course(course_id, user.id)
    documents = list_documents_for_course(user.id, course_id)
    package = get_learning_package(course_id, user.id)
    return serialize_course_space(course, documents, package, list_chapters(course_id, user.id), get_scene_packages(course_id, user.id))


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    course_id: int,
    file: UploadFile = File(...),
    document_type: str = Form("OTHER"),
    chapter_id: int | None = Form(None),
    user=Depends(require_current_user),
):
    _require_course(course_id, user.id)
    data = await file.read()
    service_file = ServiceUploadFile(file.filename or "", file.content_type, data)
    try:
        document = save_uploaded_document(user.id, course_id, service_file, document_type)
        if chapter_id is not None:
            from src.services.chapter_service import move_document
            document = move_document(document.id, course_id, user.id, chapter_id)
    except DocumentUploadError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_document", "message": str(exc)},
        ) from exc
    return serialize_document(document)


@router.delete("/documents/{document_id}", response_model=MessageResponse)
def delete_document(course_id: int, document_id: int, user=Depends(require_current_user)):
    _require_course(course_id, user.id)
    deleted = delete_document_for_user(document_id, user.id, course_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={"code": "document_not_found", "message": "The document was not found."},
        )
    return MessageResponse(message="Document deleted successfully.")


@router.post(
    "/learning-package/generate",
    response_model=LearningPackageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_learning_package(
    course_id: int,
    background_tasks: BackgroundTasks,
    user=Depends(require_current_user),
):
    _require_course(course_id, user.id)
    try:
        usage_reservation = reserve_ai_generation(user.id)
    except UsageQuotaExceededError as exc:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "quota_exceeded",
                "metric": "ai_generation",
                "limit": exc.limit,
                "used": exc.used,
                "remaining": 0,
                "resets_at": exc.resets_at.isoformat(),
                "message": str(exc),
            },
        ) from exc
    try:
        package = queue_course_package(course_id, user.id)
    except GenerationInProgressError as exc:
        release_ai_generation(usage_reservation)
        raise HTTPException(
            status_code=409,
            detail={"code": "generation_in_progress", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        release_ai_generation(usage_reservation)
        raise HTTPException(
            status_code=400,
            detail={"code": "generation_failed", "message": str(exc)},
        ) from exc
    except Exception:
        release_ai_generation(usage_reservation)
        raise
    package.usage_record_id = usage_reservation.id
    from src.database import get_db_session
    from src.models import LearningPackage
    with get_db_session() as session:
        stored_package = session.get(LearningPackage, package.id)
        if stored_package is not None:
            stored_package.usage_record_id = usage_reservation.id
    if os.getenv("LEARNING_OS_TESTING", "").lower() in {"1", "true"}:
        background_tasks.add_task(_run_generation_background_task, package.id, course_id, user.id)
    return serialize_learning_package(package)


@router.post("/generations/{scene}", response_model=LearningPackageResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_scene(scene: str, background_tasks: BackgroundTasks, course_id: int, scope_document_id: int | None = None, user=Depends(require_current_user)):
    if scene not in {"follow", "textbook", "exam"}:
        raise HTTPException(400, detail={"code": "invalid_scene", "message": "Invalid learning scene."})
    _require_course(course_id, user.id)
    entitlement = get_active_entitlement(user.id, course_id)
    reservation = None
    if entitlement is not None:
        try:
            require_scene_allowance(entitlement, scene)
        except EntitlementQuotaExceeded as exc:
            raise HTTPException(429, detail={"code": "course_quota_exceeded", "message": str(exc)}) from exc
    else:
        reservation = reserve_ai_generation(user.id)
    try:
        package = queue_course_package(course_id, user.id, scene, scope_document_id)
        package.usage_record_id = reservation.id if reservation else None
        package.entitlement_id = entitlement.id if entitlement else None
        from src.database import get_db_session
        from src.models import LearningPackage
        with get_db_session() as session:
            stored = session.get(LearningPackage, package.id)
            stored.usage_record_id = reservation.id if reservation else None
            stored.entitlement_id = entitlement.id if entitlement else None
    except Exception:
        if reservation:
            release_ai_generation(reservation)
        raise
    if os.getenv("LEARNING_OS_TESTING", "").lower() in {"1", "true"}:
        background_tasks.add_task(_run_generation_background_task, package.id, course_id, user.id, scene, scope_document_id)
    return serialize_learning_package(package)


@router.get(
    "/learning-package/{package_id}",
    response_model=LearningPackageResponse,
)
def get_learning_package_status(
    course_id: int,
    package_id: int,
    user=Depends(require_current_user),
):
    _require_course(course_id, user.id)
    package = get_learning_package_task(package_id, course_id, user.id)
    if package is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "generation_task_not_found", "message": "The generation task was not found."},
        )
    return serialize_learning_package(package)


@router.post("/assistant/query", response_model=AssistantQueryResponse)
def query_course_assistant(
    course_id: int,
    payload: AssistantQueryRequest,
    user=Depends(require_current_user),
):
    _require_course(course_id, user.id)
    try:
        if payload.scene or payload.chapter_id or payload.textbook_id:
            result = answer_course_question(course_id, user.id, payload.question, payload.current_section, scene=payload.scene, chapter_id=payload.chapter_id, textbook_id=payload.textbook_id)
        else:
            result = answer_course_question(course_id, user.id, payload.question, payload.current_section)
        consume_assistant(user.id, course_id)
    except EntitlementQuotaExceeded as exc:
        raise HTTPException(429, detail={"code": "assistant_quota_exceeded", "message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Course assistant query failed.")
        raise HTTPException(
            status_code=502,
            detail={"code": "assistant_unavailable", "message": "The course assistant is unavailable."},
        ) from exc
    return AssistantQueryResponse(answer=result.answer, source_files=result.source_files)


def _require_course(course_id, user_id):
    course = get_course_for_user(course_id, user_id)
    if course is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "course_not_found", "message": "The course was not found."},
        )
    return course


def _run_generation_background_task(package_id, course_id, user_id, scene=None, scope_document_id=None):
    try:
        if scene is None and scope_document_id is None:
            run_queued_course_package(package_id, course_id, user_id)
        else:
            run_queued_course_package(package_id, course_id, user_id, scene, scope_document_id)
    except Exception:
        logger.exception(
            "Course content generation task failed.",
            extra={"package_id": package_id, "course_id": course_id},
        )

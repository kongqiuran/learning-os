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
from src.services.analysis_service import get_learning_package, get_learning_package_task, get_scene_packages, get_scoped_packages
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
from src.services.entitlement_service import (
    EntitlementQuotaExceeded,
    get_active_entitlement,
    release_assistant,
    release_scene,
    reserve_assistant,
    reserve_scene,
)
from src.services.quota_settlement_service import release_package_quota, settle_package_quota
from src.services.task_service import fail_package_task
from src.logging_config import get_logger


router = APIRouter(prefix="/api/courses/{course_id}", tags=["course-space"])
logger = get_logger(__name__)


@router.get("/space", response_model=CourseSpaceResponse)
def get_course_space(course_id: int, user=Depends(require_current_user)):
    course = _require_course(course_id, user.id)
    documents = list_documents_for_course(user.id, course_id)
    package = get_learning_package(course_id, user.id)
    chapter_packages, document_packages = get_scoped_packages(course_id, user.id)
    chapter_completed, document_completed = get_scoped_packages(course_id, user.id, completed_only=True)
    return serialize_course_space(
        course, documents, package, list_chapters(course_id, user.id),
        get_scene_packages(course_id, user.id), chapter_packages, document_packages,
        get_scene_packages(course_id, user.id, completed_only=True), chapter_completed, document_completed,
    )


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
        raise _free_quota_http_error(exc, course_id) from exc
    try:
        package = queue_course_package(course_id, user.id, usage_record_id=usage_reservation.id, quota_source="free_monthly")
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
    if os.getenv("LEARNING_OS_TESTING", "").lower() in {"1", "true"}:
        background_tasks.add_task(_run_generation_background_task, package.id, course_id, user.id)
    return serialize_learning_package(package)


@router.post("/generations/{scene}", response_model=LearningPackageResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_scene(scene: str, background_tasks: BackgroundTasks, course_id: int, scope_document_id: int | None = None, scope_chapter_id: int | None = None, scope_unassigned: bool = False, user=Depends(require_current_user)):
    if scene not in {"follow", "textbook", "exam"}:
        raise HTTPException(400, detail={"code": "invalid_scene", "message": "Invalid learning scene."})
    _require_course(course_id, user.id)
    entitlement = get_active_entitlement(user.id, course_id)
    reservation = None
    paid_reserved = False
    if entitlement is not None:
        try:
            reserve_scene(entitlement.id, scene)
            paid_reserved = True
        except EntitlementQuotaExceeded as exc:
            raise _paid_quota_http_error(course_id, scene, str(exc)) from exc
    else:
        try:
            reservation = reserve_ai_generation(user.id)
        except UsageQuotaExceededError as exc:
            raise _free_quota_http_error(exc, course_id, scene) from exc
    try:
        package = queue_course_package(
            course_id,
            user.id,
            scene,
            scope_document_id,
            scope_chapter_id,
            scope_unassigned,
            reservation.id if reservation else None,
            entitlement.id if entitlement else None,
            "course_entitlement" if entitlement else "free_monthly",
        )
    except GenerationInProgressError as exc:
        _release_unattached_quota(reservation, entitlement.id if paid_reserved and entitlement else None, scene)
        raise HTTPException(409, detail={"code": "generation_in_progress", "message": str(exc)}) from exc
    except ValueError as exc:
        _release_unattached_quota(reservation, entitlement.id if paid_reserved and entitlement else None, scene)
        raise HTTPException(400, detail={"code": "invalid_generation_scope", "message": str(exc)}) from exc
    except Exception:
        _release_unattached_quota(reservation, entitlement.id if paid_reserved and entitlement else None, scene)
        raise
    if os.getenv("LEARNING_OS_TESTING", "").lower() in {"1", "true"}:
        background_tasks.add_task(_run_generation_background_task, package.id, course_id, user.id, scene, scope_document_id, scope_chapter_id, scope_unassigned)
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
    assistant_entitlement_id = None
    try:
        assistant_entitlement_id = reserve_assistant(user.id, course_id)
        if payload.scene or payload.chapter_id or payload.textbook_id or payload.scope_unassigned:
            result = answer_course_question(course_id, user.id, payload.question, payload.current_section, scene=payload.scene, chapter_id=payload.chapter_id, textbook_id=payload.textbook_id, scope_unassigned=payload.scope_unassigned)
        else:
            result = answer_course_question(course_id, user.id, payload.question, payload.current_section)
    except EntitlementQuotaExceeded as exc:
        raise _paid_quota_http_error(course_id, "assistant", str(exc)) from exc
    except Exception as exc:
        if assistant_entitlement_id is not None:
            release_assistant(assistant_entitlement_id)
        logger.exception(
            "Course assistant query failed.",
            extra={
                "event": "assistant.query.failed",
                "user_id": user.id,
                "task_id": None,
                "document_id": payload.textbook_id,
                "course_id": course_id,
                "scene": payload.scene or "assistant",
                "exception": exc,
            },
        )
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


def _run_generation_background_task(package_id, course_id, user_id, scene=None, scope_document_id=None, scope_chapter_id=None, scope_unassigned=False):
    try:
        if scene is None and scope_document_id is None and scope_chapter_id is None and not scope_unassigned:
            run_queued_course_package(package_id, course_id, user_id)
        else:
            run_queued_course_package(package_id, course_id, user_id, scene, scope_document_id, scope_chapter_id, scope_unassigned)
        from src.database import get_db_session
        with get_db_session() as session:
            settle_package_quota(session, package_id)
    except Exception as exc:
        from src.database import get_db_session
        from src.models import LearningPackage
        with get_db_session() as session:
            package = session.get(LearningPackage, package_id)
            if package is not None and package.status != "failed":
                fail_package_task(session, package, user_id, type(exc).__name__, str(exc) or type(exc).__name__)
            release_package_quota(session, package_id)
        logger.exception(
            "Course content generation task failed.",
            extra={
                "event": "background_generation.failed",
                "user_id": user_id,
                "task_id": package.task_id if package is not None else None,
                "document_id": scope_document_id,
                "package_id": package_id,
                "course_id": course_id,
                "scene": scene or "legacy",
                "exception": exc,
            },
        )


def _free_quota_http_error(exc, course_id, scene=None):
    return HTTPException(
        status_code=429,
        detail={
            "code": "insufficient_credits",
            "message": "The monthly AI generation quota has been reached.",
            "quota_source": "free_monthly",
            "metric": "ai_generation",
            "scene": scene,
            "course_id": int(course_id),
            "limit": exc.limit,
            "used": exc.used,
            "remaining": 0,
            "resets_at": exc.resets_at.isoformat(),
            "can_purchase": True,
            "purchase_url": f"/pricing?course_id={int(course_id)}" + (f"&scene={scene}" if scene else ""),
        },
    )


def _paid_quota_http_error(course_id, scene, message):
    return HTTPException(
        status_code=429,
        detail={
            "code": "insufficient_credits",
            "message": message,
            "quota_source": "course_entitlement",
            "metric": f"{scene}_generation" if scene != "assistant" else "assistant_query",
            "scene": scene,
            "course_id": int(course_id),
            "remaining": 0,
            "can_purchase": True,
            "purchase_url": f"/pricing?course_id={int(course_id)}&scene={scene}",
        },
    )


def _release_unattached_quota(reservation, entitlement_id, scene):
    if reservation is not None:
        release_ai_generation(reservation)
    if entitlement_id is not None:
        release_scene(entitlement_id, scene)

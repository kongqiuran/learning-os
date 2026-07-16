import logging

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
from src.services.analysis_service import get_learning_package, get_learning_package_task
from src.services.course_service import get_course_for_user
from src.services.document_service import (
    DocumentUploadError,
    delete_document_for_user,
    list_documents_for_course,
    save_uploaded_document,
)


router = APIRouter(prefix="/api/courses/{course_id}", tags=["course-space"])
logger = logging.getLogger(__name__)


@router.get("/space", response_model=CourseSpaceResponse)
def get_course_space(course_id: int, user=Depends(require_current_user)):
    course = _require_course(course_id, user.id)
    documents = list_documents_for_course(user.id, course_id)
    package = get_learning_package(course_id, user.id)
    return serialize_course_space(course, documents, package)


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    course_id: int,
    file: UploadFile = File(...),
    document_type: str = Form("OTHER"),
    user=Depends(require_current_user),
):
    _require_course(course_id, user.id)
    data = await file.read()
    service_file = ServiceUploadFile(file.filename or "", file.content_type, data)
    try:
        document = save_uploaded_document(user.id, course_id, service_file, document_type)
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
        package = queue_course_package(course_id, user.id)
    except GenerationInProgressError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "generation_in_progress", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "generation_failed", "message": str(exc)},
        ) from exc
    background_tasks.add_task(
        _run_generation_background_task,
        package.id,
        course_id,
        user.id,
    )
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
        result = answer_course_question(
            course_id,
            user.id,
            payload.question,
            payload.current_section,
        )
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


def _run_generation_background_task(package_id, course_id, user_id):
    try:
        run_queued_course_package(package_id, course_id, user_id)
    except Exception:
        logger.exception(
            "Course content generation task failed.",
            extra={"package_id": package_id, "course_id": course_id},
        )

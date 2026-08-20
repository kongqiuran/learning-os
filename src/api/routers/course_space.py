# 文件说明：课程空间的文档主链路 API。
# APIRouter、BackgroundTasks、Depends、File、Form、HTTPException、UploadFile、status 都来自 FastAPI：
# - APIRouter 用来声明一组接口路由；
# - Depends 用来声明登录依赖；
# - File/Form/UploadFile 用来接收 multipart 文件上传；
# - BackgroundTasks 只在测试环境里模拟 Worker 执行，生产环境真正生成由 worker.py 处理。
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


# prefix 表示下面所有接口都会自动加上 /api/courses/{course_id}。
# {course_id} 是 FastAPI 的路径参数写法，函数参数里同名的 course_id 会自动收到这个值。
router = APIRouter(prefix="/api/courses/{course_id}", tags=["course-space"])
logger = get_logger(__name__)


@router.get("/space", response_model=CourseSpaceResponse)
def get_course_space(course_id: int, user=Depends(require_current_user)):
    # GET /space 是课程空间的聚合查询。
    # user=Depends(require_current_user) 表示 FastAPI 会先执行 require_current_user，确认 session cookie 已登录。
    # 这里不会解析文档，只是把课程、资料、章节、学习包任务状态从数据库查出来给前端展示。
    course = _require_course(course_id, user.id)
    documents = list_documents_for_course(user.id, course_id)
    package = get_learning_package(course_id, user.id)
    # scoped packages 指按章节或单文档范围保存的学习包。
    # 例如 follow 场景按 chapter_id，textbook 场景按 scope_document_id。
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
    # UploadFile 来自 FastAPI，代表浏览器上传的文件；File(...) 表示这个字段必须来自 multipart file。
    file: UploadFile = File(...),
    # Form 来自 FastAPI，表示 document_type/chapter_id 是 multipart 表单字段，不是 JSON body。
    document_type: str = Form("OTHER"),
    chapter_id: int | None = Form(None),
    user=Depends(require_current_user),
):
    # 上传只做校验、落盘、写 Document 记录；根据 docs/文档交互与接口链路.md，上传阶段不会解析或调用 AI。
    _require_course(course_id, user.id)
    # await 是 Python 异步语法；file.read() 是异步读取上传文件内容，避免阻塞 FastAPI 事件循环。
    data = await file.read()
    # ServiceUploadFile 是本项目适配器对象，把 FastAPI 的 UploadFile 转成 document_service 能识别的 name/type/read 接口。
    service_file = ServiceUploadFile(file.filename or "", file.content_type, data)
    try:
        document = save_uploaded_document(user.id, course_id, service_file, document_type)
        if chapter_id is not None:
            # 章节绑定只改 Document.chapter_id，不会重解析文件。
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
    # POST /generations/{scene} 是“点击整理”的入口。
    # 这个接口只创建 LearningPackage(status=pending) 并预扣额度；真正解析文档和调用 AI 由 worker.py 领取任务后执行。
    if scene not in {"follow", "textbook", "exam"}:
        raise HTTPException(400, detail={"code": "invalid_scene", "message": "Invalid learning scene."})
    _require_course(course_id, user.id)
    # entitlement 表示单课购买权益；没有权益时走免费月额度。
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
        # queue_course_package 来自 generation_adapter：它会检查同课程+同场景+同范围是否已有 pending/processing，
        # 然后调用 analysis_service.create_learning_package_task 写入 LearningPackage 任务。
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
    # 课程助手不会重新解析文件。
    # 它优先读取已完成 LearningPackage 的章节内容，再补充同范围 DocumentAnalysis，最后交给 LLM 回答。
    _require_course(course_id, user.id)
    assistant_entitlement_id = None
    try:
        # reserve_assistant 会扣一次助手额度；如果后续异常，会在 except 中释放。
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

# 文件说明：课程基础接口。APIRouter/Depends/HTTPException/status 来自 FastAPI；这里负责首页课程摘要、建课、查课和删课。
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import require_current_user
from src.api.schemas import (
    CourseCreateRequest,
    CourseDetailResponse,
    CourseListResponse,
    CourseSummaryResponse,
    DashboardResponse,
    MessageResponse,
)
from src.api.serializers import serialize_course_detail, serialize_course_summary
from src.services.analysis_service import get_learning_package
from src.services.course_service import (
    create_course,
    delete_course_for_user,
    get_course_for_user,
    list_courses_for_user,
)
from src.services.document_service import list_documents_for_course


# 课程接口的 prefix 是 /api，因为 dashboard、courses 都是产品基础入口。
router = APIRouter(prefix="/api", tags=["courses"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(user=Depends(require_current_user)):
    # dashboard 是登录后首页接口，返回课程数量、资料数量和课程卡片列表。
    courses = _list_course_summaries(user.id)
    return DashboardResponse(
        course_count=len(courses),
        document_count=sum(course.document_count for course in courses),
        courses=courses,
    )


@router.get("/courses", response_model=CourseListResponse)
def get_courses(user=Depends(require_current_user)):
    return CourseListResponse(courses=_list_course_summaries(user.id))


@router.post(
    "/courses",
    response_model=CourseDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_course(payload: CourseCreateRequest, user=Depends(require_current_user)):
    try:
        course = create_course(user.id, payload.name, payload.description)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_course", "message": str(exc)},
        ) from exc
    return serialize_course_detail(course, [], None)


@router.get("/courses/{course_id}", response_model=CourseDetailResponse)
def get_course(course_id: int, user=Depends(require_current_user)):
    course = get_course_for_user(course_id, user.id)
    if course is None:
        raise _course_not_found()
    return _serialize_course(course, user.id, detail=True)


@router.delete("/courses/{course_id}", response_model=MessageResponse)
def delete_course(course_id: int, user=Depends(require_current_user)):
    deleted = delete_course_for_user(course_id, user.id)
    if not deleted:
        raise _course_not_found()
    return MessageResponse(message="Course deleted successfully.")


def _list_course_summaries(user_id):
    # 列表推导式是 Python 语法：对每门课程调用 _serialize_course，生成课程摘要数组。
    return [_serialize_course(course, user_id) for course in list_courses_for_user(user_id)]


def _serialize_course(course, user_id, detail=False):
    # 课程摘要会同时读取资料和最近学习包，用 serializer 计算 document_count 和 updated_at。
    documents = list_documents_for_course(user_id, course.id)
    learning_package = get_learning_package(course.id, user_id)
    serializer = serialize_course_detail if detail else serialize_course_summary
    return serializer(course, documents, learning_package)


def _course_not_found():
    return HTTPException(
        status_code=404,
        detail={"code": "course_not_found", "message": "The course was not found."},
    )

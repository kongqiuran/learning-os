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


router = APIRouter(prefix="/api", tags=["courses"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(user=Depends(require_current_user)):
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
    return [_serialize_course(course, user_id) for course in list_courses_for_user(user_id)]


def _serialize_course(course, user_id, detail=False):
    documents = list_documents_for_course(user_id, course.id)
    learning_package = get_learning_package(course.id, user_id)
    serializer = serialize_course_detail if detail else serialize_course_summary
    return serializer(course, documents, learning_package)


def _course_not_found():
    return HTTPException(
        status_code=404,
        detail={"code": "course_not_found", "message": "The course was not found."},
    )

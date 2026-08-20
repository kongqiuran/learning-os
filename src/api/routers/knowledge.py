# 文件说明：知识点接口。
# APIRouter/Depends/HTTPException 来自 FastAPI；知识点没有独立表，而是从 DocumentAnalysis.topics 派生出来。
from fastapi import APIRouter, Depends, HTTPException

from src.api.adapters.knowledge_adapter import (
    get_knowledge_item,
    list_course_knowledge,
    mark_knowledge_viewed,
)
from src.api.dependencies import require_current_user
from src.api.schemas import (
    KnowledgeCourseResponse,
    KnowledgeDetailResponse,
    KnowledgeListResponse,
    KnowledgeViewedResponse,
)
from src.api.serializers import serialize_knowledge_detail, serialize_knowledge_summary
from src.services.course_service import get_course_for_user


router = APIRouter(prefix="/api", tags=["knowledge"])


@router.get("/courses/{course_id}/knowledge", response_model=KnowledgeListResponse)
def get_course_knowledge(course_id: int, user=Depends(require_current_user)):
    # 列表接口会把课程下每份 DocumentAnalysis.topics 展开成知识点。
    # 如果某份资料只上传但没跑过整理，就没有 DocumentAnalysis，因此也不会出现在知识点列表。
    course = get_course_for_user(course_id, user.id)
    if course is None:
        raise _knowledge_not_found()
    items = list_course_knowledge(course, user.id)
    return KnowledgeListResponse(
        course=KnowledgeCourseResponse(id=course.id, name=course.name),
        knowledge_count=len(items),
        items=[serialize_knowledge_summary(item) for item in items],
    )


@router.get("/knowledge/{knowledge_id}", response_model=KnowledgeDetailResponse)
def get_knowledge(knowledge_id: str, user=Depends(require_current_user)):
    # knowledge_id 是派生 ID，形如 analysis-{分析ID}-topic-{序号}。
    # 后端会反解析这个 ID，定位到 DocumentAnalysis 中对应的 topic。
    item = get_knowledge_item(knowledge_id, user.id)
    if item is None:
        raise _knowledge_not_found()
    return serialize_knowledge_detail(item)


@router.patch("/knowledge/{knowledge_id}/viewed", response_model=KnowledgeViewedResponse)
def patch_knowledge_viewed(knowledge_id: str, user=Depends(require_current_user)):
    # 标记已读不会改 DocumentAnalysis 本身，而是记录用户对这个派生知识点的查看状态。
    viewed_at = mark_knowledge_viewed(knowledge_id, user.id)
    if viewed_at is None:
        raise _knowledge_not_found()
    return KnowledgeViewedResponse(
        knowledge_id=knowledge_id,
        viewed=True,
        viewed_at=viewed_at,
    )


def _knowledge_not_found():
    return HTTPException(
        status_code=404,
        detail={"code": "knowledge_not_found", "message": "The knowledge item was not found."},
    )

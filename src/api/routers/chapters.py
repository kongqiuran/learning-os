from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import require_current_user
from src.api.schemas import ChapterCreateRequest, ChapterDeleteRequest, ChapterResponse, ChapterUpdateRequest, DocumentMoveRequest, DocumentResponse, MessageResponse
from src.api.serializers import serialize_document
from src.services.chapter_service import create_chapter, delete_chapter, list_chapters, move_document, update_chapter
from src.services.document_service import list_documents_for_course


router = APIRouter(prefix="/api/courses/{course_id}", tags=["chapters"])


def _serialize(chapter, documents):
    return ChapterResponse(id=chapter.id, title=chapter.title, position=chapter.position, document_count=sum(1 for item in documents if item.chapter_id == chapter.id), created_at=chapter.created_at, updated_at=chapter.updated_at)


@router.get("/chapters", response_model=list[ChapterResponse])
def get_chapters(course_id: int, user=Depends(require_current_user)):
    documents = list_documents_for_course(user.id, course_id)
    return [_serialize(item, documents) for item in list_chapters(course_id, user.id)]


@router.post("/chapters", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
def post_chapter(course_id: int, payload: ChapterCreateRequest, user=Depends(require_current_user)):
    chapter = create_chapter(course_id, user.id, payload.title)
    if chapter is None:
        raise HTTPException(404, detail={"code": "course_not_found", "message": "Course not found."})
    return _serialize(chapter, [])


@router.patch("/chapters/{chapter_id}", response_model=ChapterResponse)
def patch_chapter(course_id: int, chapter_id: int, payload: ChapterUpdateRequest, user=Depends(require_current_user)):
    chapter = update_chapter(chapter_id, course_id, user.id, payload.title, payload.position)
    if chapter is None:
        raise HTTPException(404, detail={"code": "chapter_not_found", "message": "Chapter not found."})
    return _serialize(chapter, list_documents_for_course(user.id, course_id))


@router.delete("/chapters/{chapter_id}", response_model=MessageResponse)
def remove_chapter(course_id: int, chapter_id: int, payload: ChapterDeleteRequest, user=Depends(require_current_user)):
    try:
        deleted = delete_chapter(chapter_id, course_id, user.id, payload.material_action)
    except ValueError as exc:
        raise HTTPException(400, detail={"code": "chapter_action_required", "message": str(exc)}) from exc
    if not deleted:
        raise HTTPException(404, detail={"code": "chapter_not_found", "message": "Chapter not found."})
    return MessageResponse(message="Chapter deleted.")


@router.patch("/documents/{document_id}/chapter", response_model=DocumentResponse)
def patch_document_chapter(course_id: int, document_id: int, payload: DocumentMoveRequest, user=Depends(require_current_user)):
    document = move_document(document_id, course_id, user.id, payload.chapter_id)
    if document is None:
        raise HTTPException(404, detail={"code": "document_not_found", "message": "Document not found."})
    return serialize_document(document)

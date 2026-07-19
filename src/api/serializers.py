from src.api.schemas import (
    CourseDetailResponse,
    CourseSpaceResponse,
    CourseSummaryResponse,
    ChapterResponse,
    DocumentResponse,
    LearningPackageResponse,
    KnowledgeDetailResponse,
    KnowledgeSummaryResponse,
)


def serialize_course_summary(course, documents, learning_package=None):
    timestamps = [course.created_at]
    timestamps.extend(document.uploaded_at for document in documents)
    if learning_package is not None:
        timestamps.append(learning_package.created_at)

    return CourseSummaryResponse(
        id=course.id,
        name=course.name,
        description=course.description,
        created_at=course.created_at,
        updated_at=max(timestamps),
        document_count=len(documents),
    )


def serialize_course_detail(course, documents, learning_package=None):
    summary = serialize_course_summary(course, documents, learning_package)
    return CourseDetailResponse(**summary.model_dump())


def serialize_document(document):
    return DocumentResponse(
        id=document.id,
        name=document.original_filename,
        mime_type=document.mime_type,
        file_size=document.file_size,
        status=document.processing_status,
        document_type=document.document_type,
        chapter_id=getattr(document, "chapter_id", None),
        uploaded_at=document.uploaded_at,
    )


def serialize_learning_package(package):
    if package is None:
        return None
    content = package.content_json if isinstance(package.content_json, dict) else {}
    return LearningPackageResponse(
        id=package.id,
        status=package.status,
        version=package.version,
        content=content,
        current_stage=getattr(package, "current_stage", None),
        retry_count=getattr(package, "retry_count", 0) or 0,
        error_type=getattr(package, "error_type", None),
        error_detail=getattr(package, "error_detail", None),
        created_at=package.created_at,
        scene=getattr(package, "scene", "legacy") or "legacy",
        scope_document_id=getattr(package, "scope_document_id", None),
        scope_chapter_id=getattr(package, "scope_chapter_id", None),
        scope_unassigned=bool(getattr(package, "scope_unassigned", False)),
        scope_kind=getattr(package, "scope_kind", "course") or "course",
        scope_key=getattr(package, "scope_key", "course") or "course",
        source_fingerprint=getattr(package, "source_fingerprint", None),
        prompt_version=getattr(package, "prompt_version", None),
        is_stale=bool(getattr(package, "is_stale", False)),
    )


def serialize_course_space(course, documents, learning_package, chapters=None, scene_packages=None, chapter_packages=None, document_packages=None, scene_completed_packages=None, chapter_completed_packages=None, document_completed_packages=None):
    return CourseSpaceResponse(
        course=serialize_course_detail(course, documents, learning_package),
        documents=[serialize_document(document) for document in documents],
        learning_package=serialize_learning_package(learning_package),
        chapters=[ChapterResponse(id=item.id, title=item.title, position=item.position, document_count=sum(1 for document in documents if getattr(document, "chapter_id", None) == item.id), created_at=item.created_at, updated_at=item.updated_at) for item in (chapters or [])],
        scene_packages={key: serialize_learning_package(value) for key, value in (scene_packages or {}).items()},
        scene_completed_packages={key: serialize_learning_package(value) for key, value in (scene_completed_packages or {}).items()},
        chapter_packages={str(key): serialize_learning_package(value) for key, value in (chapter_packages or {}).items()},
        chapter_completed_packages={str(key): serialize_learning_package(value) for key, value in (chapter_completed_packages or {}).items()},
        document_packages={str(key): serialize_learning_package(value) for key, value in (document_packages or {}).items()},
        document_completed_packages={str(key): serialize_learning_package(value) for key, value in (document_completed_packages or {}).items()},
    )


def serialize_knowledge_summary(item):
    return KnowledgeSummaryResponse(
        id=item.id,
        title=item.title,
        content=item.content,
        importance=item.importance,
        course_id=item.course_id,
        course_name=item.course_name,
        document_id=item.document_id,
        source_file=item.source_file,
        updated_at=item.updated_at,
        viewed=item.viewed,
        viewed_at=item.viewed_at,
    )


def serialize_knowledge_detail(item):
    summary = serialize_knowledge_summary(item)
    return KnowledgeDetailResponse(
        **summary.model_dump(),
        core_explanation=item.core_explanation,
        exam_value=item.exam_value,
        must_master=item.must_master,
        memory_tips=item.memory_tips,
        reason=item.reason,
        source_formulas=item.source_formulas,
        source_errors=item.source_errors,
    )

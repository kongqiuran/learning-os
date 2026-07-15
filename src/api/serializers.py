from src.api.schemas import (
    CourseDetailResponse,
    CourseSpaceResponse,
    CourseSummaryResponse,
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
        created_at=package.created_at,
    )


def serialize_course_space(course, documents, learning_package):
    return CourseSpaceResponse(
        course=serialize_course_detail(course, documents, learning_package),
        documents=[serialize_document(document) for document in documents],
        learning_package=serialize_learning_package(learning_package),
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

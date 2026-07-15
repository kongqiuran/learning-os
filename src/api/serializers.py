from src.api.schemas import CourseDetailResponse, CourseSummaryResponse


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

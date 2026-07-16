from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(LoginRequest):
    confirm_password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str


class CourseCreateRequest(BaseModel):
    name: str = Field(max_length=200)
    description: str | None = None


class CourseSummaryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    document_count: int


class CourseDetailResponse(CourseSummaryResponse):
    pass


class CourseListResponse(BaseModel):
    courses: list[CourseSummaryResponse]


class DashboardResponse(BaseModel):
    course_count: int
    document_count: int
    courses: list[CourseSummaryResponse]


class DocumentResponse(BaseModel):
    id: int
    name: str
    mime_type: str
    file_size: int
    status: str
    document_type: str
    uploaded_at: datetime


class LearningPackageResponse(BaseModel):
    id: int
    status: str
    version: int
    content: dict[str, Any]
    current_stage: str | None = None
    retry_count: int = 0
    error_type: str | None = None
    error_detail: str | None = None
    created_at: datetime


class CourseSpaceResponse(BaseModel):
    course: CourseDetailResponse
    documents: list[DocumentResponse]
    learning_package: LearningPackageResponse | None


class AssistantQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    current_section: str | None = Field(default=None, max_length=200)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        if not value.strip():
            raise ValueError("Question must not be blank.")
        return value.strip()


class AssistantQueryResponse(BaseModel):
    answer: str
    source_files: list[str]


class KnowledgeCourseResponse(BaseModel):
    id: int
    name: str


class KnowledgeSummaryResponse(BaseModel):
    id: str
    title: str
    content: str
    importance: int | None
    course_id: int
    course_name: str
    document_id: int
    source_file: str
    updated_at: datetime
    viewed: bool
    viewed_at: datetime | None


class KnowledgeDetailResponse(KnowledgeSummaryResponse):
    core_explanation: str
    exam_value: str
    must_master: list[Any]
    memory_tips: str
    reason: str
    source_formulas: list[Any]
    source_errors: list[Any]


class KnowledgeListResponse(BaseModel):
    course: KnowledgeCourseResponse
    knowledge_count: int
    items: list[KnowledgeSummaryResponse]


class KnowledgeViewedResponse(BaseModel):
    knowledge_id: str
    viewed: bool
    viewed_at: datetime

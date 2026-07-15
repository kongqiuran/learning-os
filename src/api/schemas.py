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

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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

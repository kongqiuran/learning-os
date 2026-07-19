from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(LoginRequest):
    confirm_password: str
    accepted_terms: bool = False


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserResponse


class AccountDeletionRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)
    confirmation: str = Field(min_length=1, max_length=64)


class AccountDeletionResponse(BaseModel):
    deletion_id: str
    status: str
    message: str


class PrivacyPolicyCurrentResponse(BaseModel):
    policy_version: str


class PrivacyConsentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool


class PrivacyConsentResponse(BaseModel):
    policy_version: str
    accepted_at: datetime
    created: bool


class PrivacyConsentStatusResponse(BaseModel):
    current_version: str
    accepted: bool
    requires_reconsent: bool


class AiGenerationUsageResponse(BaseModel):
    used: int
    limit: int
    remaining: int
    resets_at: datetime


class UsageSummaryResponse(BaseModel):
    plan: str
    ai_generations: AiGenerationUsageResponse
    course_entitlements: list["CourseEntitlementResponse"] = Field(default_factory=list)


class CourseEntitlementResponse(BaseModel):
    id: int
    course_id: int
    course_name: str
    product_code: str
    amount_cents: int
    status: str
    activated_at: datetime
    expires_at: datetime
    follow_remaining: int
    textbook_remaining: int
    exam_remaining: int
    assistant_remaining: int


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
    chapter_id: int | None = None
    uploaded_at: datetime


class ChapterCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ChapterUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    position: int | None = Field(default=None, ge=0)


class ChapterDeleteRequest(BaseModel):
    material_action: str


class DocumentMoveRequest(BaseModel):
    chapter_id: int | None = None


class ChapterResponse(BaseModel):
    id: int
    title: str
    position: int
    document_count: int
    created_at: datetime
    updated_at: datetime


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
    scene: str = "legacy"
    scope_document_id: int | None = None
    scope_chapter_id: int | None = None
    scope_unassigned: bool = False
    scope_kind: str = "course"
    scope_key: str = "course"
    source_fingerprint: str | None = None
    prompt_version: str | None = None
    is_stale: bool = False


class CourseSpaceResponse(BaseModel):
    course: CourseDetailResponse
    documents: list[DocumentResponse]
    learning_package: LearningPackageResponse | None
    chapters: list[ChapterResponse] = Field(default_factory=list)
    scene_packages: dict[str, LearningPackageResponse | None] = Field(default_factory=dict)
    scene_completed_packages: dict[str, LearningPackageResponse | None] = Field(default_factory=dict)
    chapter_packages: dict[str, LearningPackageResponse] = Field(default_factory=dict)
    chapter_completed_packages: dict[str, LearningPackageResponse] = Field(default_factory=dict)
    document_packages: dict[str, LearningPackageResponse] = Field(default_factory=dict)
    document_completed_packages: dict[str, LearningPackageResponse] = Field(default_factory=dict)


class AssistantQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    current_section: str | None = Field(default=None, max_length=200)
    scene: str | None = Field(default=None, max_length=20)
    chapter_id: int | None = None
    textbook_id: int | None = None
    scope_unassigned: bool = False

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

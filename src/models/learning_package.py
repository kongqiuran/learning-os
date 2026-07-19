from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.models.user import utc_now


class LearningPackage(Base):
    __tablename__ = "learning_packages"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_learning_packages_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scene: Mapped[str] = mapped_column(String(20), nullable=False, default="legacy", index=True)
    scope_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    scope_chapter_id: Mapped[int | None] = mapped_column(ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True, index=True)
    scope_unassigned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scope_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="course", index=True)
    scope_key: Mapped[str] = mapped_column(String(80), nullable=False, default="course", index=True)
    source_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    usage_record_id: Mapped[int | None] = mapped_column(ForeignKey("usage_records.id", ondelete="SET NULL"), nullable=True)
    entitlement_id: Mapped[int | None] = mapped_column(ForeignKey("course_entitlements.id", ondelete="SET NULL"), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    task_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    course: Mapped["Course"] = relationship(back_populates="learning_packages")

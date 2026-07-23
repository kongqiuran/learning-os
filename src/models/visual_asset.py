from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.models.user import utc_now


class VisualAsset(Base):
    __tablename__ = "visual_assets"
    __table_args__ = (
        CheckConstraint(
            "target_type IN "
            "('knowledge_item', 'chapter', 'course_summary', 'exam_point')",
            name="ck_visual_assets_target_type",
        ),
        CheckConstraint(
            "type IN ('mindmap', 'flowchart', 'diagram', 'image')",
            name="ck_visual_assets_type",
        ),
        CheckConstraint(
            "generator IN ('mermaid', 'svg', 'image')",
            name="ck_visual_assets_generator",
        ),
        CheckConstraint(
            "status IN ('pending', 'generating', 'completed', 'failed')",
            name="ck_visual_assets_status",
        ),
        UniqueConstraint(
            "user_id",
            "target_type",
            "target_id",
            "type",
            "generator",
            "source_hash",
            name="uq_visual_assets_target_version",
        ),
        Index(
            "ix_visual_assets_target_lookup",
            "user_id",
            "target_type",
            "target_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    target_id: Mapped[str] = mapped_column(String(160), nullable=False)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    generator: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    target_snapshot: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        unique=True,
        index=True,
        nullable=True,
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    task_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    task: Mapped["Task | None"] = relationship(lazy="joined")

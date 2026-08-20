# 文件说明：Task 数据库模型。它是前端通用任务视图，用统一 status/progress/current_stage 展示学习包或配图任务进度。
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.models.user import utc_now


class Task(Base):
    # Task 是“前端统一看的任务进度”。
    # 不管底层是 LearningPackage 还是 VisualAsset，都可以同步到 Task 风格的 status/progress/stage。
    __tablename__ = "tasks"
    __table_args__ = (
        # UniqueConstraint 保证一个资源只有一个任务视图，避免前端轮询时看到重复任务。
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED')",
            name="ck_tasks_status",
        ),
        CheckConstraint(
            "progress >= 0 AND progress <= 100",
            name="ck_tasks_progress",
        ),
        UniqueConstraint("resource_type", "resource_id", name="uq_tasks_resource"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False)
    task_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # resource_type/resource_id 指向真实业务资源。
    # 例如 resource_type="learning_package"，resource_id 就是 LearningPackage.id。
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()
    course: Mapped["Course"] = relationship()

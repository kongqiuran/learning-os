# 文件说明：Document 数据库模型。Mapped/mapped_column/relationship 来自 SQLAlchemy ORM，用 Python 类描述 documents 表。
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from src.database.base import Base
from src.models.user import utc_now


class Document(Base):
    # Document 表示“用户上传的一份原始资料”。
    # 上传后 status=uploaded；只有 Worker 生成学习包时才会把它改成 processing/completed/failed。
    __tablename__ = "documents"
    __table_args__ = (
        # CheckConstraint 来自 SQLAlchemy，用数据库约束保证 status/document_type 只能取允许值，防止脏数据写入。
        CheckConstraint(
            "status IN ('uploaded', 'processing', 'completed', 'failed')",
            name="ck_documents_status",
        ),
        CheckConstraint(
            "document_type IN ('TEXTBOOK', 'SLIDES', 'EXAM', 'HOMEWORK', 'NOTES', 'OTHER')",
            name="ck_documents_document_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False)
    chapter_id: Mapped[int | None] = mapped_column(ForeignKey("chapters.id", ondelete="SET NULL"), index=True, nullable=True)
    # original_filename 是用户看到的原文件名；stored_filename/file_path 是服务器实际保存位置。
    # 分开保存可以避免用户文件名冲突，也方便后端按用户和课程隔离存储。
    original_filename: Mapped[str] = mapped_column("filename", String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="application/octet-stream",
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_status: Mapped[str] = mapped_column(
        "status",
        String(20),
        default="uploaded",
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(String(20), default="OTHER", nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    filename = synonym("original_filename")
    status = synonym("processing_status")
    created_at = synonym("uploaded_at")

    user: Mapped["User"] = relationship(back_populates="documents")
    course: Mapped["Course"] = relationship(back_populates="documents")
    chapter: Mapped["Chapter | None"] = relationship(back_populates="documents")
    analysis: Mapped["DocumentAnalysis | None"] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )
    pages: Mapped[list["DocumentPage"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentPage.page_number",
    )

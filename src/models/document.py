from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from src.database.base import Base
from src.models.user import utc_now


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
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
    analysis: Mapped["DocumentAnalysis | None"] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )

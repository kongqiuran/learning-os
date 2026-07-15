from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base
from src.models.user import utc_now


class KnowledgeView(Base):
    """MVP-only view state.

    The table is currently created through create_all for the MVP. A formal deployment
    must move this schema change to an Alembic migration before multi-environment rollout.
    """

    __tablename__ = "knowledge_views"
    __table_args__ = (
        UniqueConstraint("user_id", "knowledge_key", name="uq_knowledge_views_user_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    knowledge_key: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

# 文件说明：KnowledgeView 数据库模型。知识点本身是派生的，这张表只保存某个用户是否看过某个 knowledge_key。
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base
from src.models.user import utc_now


class KnowledgeView(Base):
    # KnowledgeView 不保存知识点正文，只保存用户是否看过某个派生 knowledge_key。
    # 这样 DocumentAnalysis.topics 仍然是公共分析结果，用户个人状态单独存放。
    """MVP-only view state.

    The table is currently created through create_all for the MVP. A formal deployment
    must move this schema change to an Alembic migration before multi-environment rollout.
    """

    __tablename__ = "knowledge_views"
    __table_args__ = (
        # UniqueConstraint 来自 SQLAlchemy，保证同一用户同一知识点只有一条已读记录。
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

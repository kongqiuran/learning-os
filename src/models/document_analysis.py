# 文件说明：DocumentAnalysis 数据库模型。每份已解析资料对应一条分析记录，知识点列表就是从 topics 字段派生出来的。
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.models.user import utc_now


class DocumentAnalysis(Base):
    # DocumentAnalysis 是“单文档理解结果”。
    # 一份 Document 只对应一条 DocumentAnalysis；已有分析可被后续学习包和课程助手复用。
    __tablename__ = "document_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    # summary/topics/importance_map 是前端知识点和课程助手最常用的结构化结果。
    # JSON 是 SQLAlchemy 字段类型，SQLite 中会以 JSON 文本形式保存 Python list/dict。
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    topics: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    importance_map: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    analysis_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="analysis")

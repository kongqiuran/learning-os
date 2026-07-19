from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.models.user import utc_now


class PaymentOrder(Base):
    __tablename__ = "payment_orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'paid', 'cancelled')",
            name="ck_payment_orders_status",
        ),
        UniqueConstraint(
            "user_id",
            "request_key",
            name="uq_payment_orders_user_request_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False)
    product_code: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    product_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True, nullable=False)
    request_key: Mapped[str] = mapped_column(String(120), nullable=False)
    entitlement_id: Mapped[int | None] = mapped_column(ForeignKey("course_entitlements.id", ondelete="SET NULL"), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    operator_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
    course: Mapped["Course"] = relationship()
    entitlement: Mapped["CourseEntitlement | None"] = relationship()

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from src.billing.product_catalog import get_billing_product
from src.database import get_db_session
from src.models import Course, CourseEntitlement, PaymentOrder


class BillingProductNotFoundError(ValueError):
    pass


class BillingProductInactiveError(ValueError):
    pass


class PaymentOrderNotFoundError(ValueError):
    pass


class PaymentOrderCourseNotFoundError(ValueError):
    pass


class PaymentOrderStateError(ValueError):
    pass


def create_payment_order(user_id, course_id, product_code, request_key):
    normalized_request_key = str(request_key).strip()
    if not normalized_request_key:
        raise ValueError("A request key is required.")

    product = get_billing_product(product_code, include_inactive=True)
    if product is None:
        raise BillingProductNotFoundError("The billing product does not exist.")
    if not product.active:
        raise BillingProductInactiveError("The billing product is not available for purchase.")

    try:
        with get_db_session() as session:
            existing = session.scalar(
                select(PaymentOrder).where(
                    PaymentOrder.user_id == int(user_id),
                    PaymentOrder.request_key == normalized_request_key,
                )
            )
            if existing is not None:
                return existing

            course = session.scalar(
                select(Course).where(
                    Course.id == int(course_id),
                    Course.user_id == int(user_id),
                )
            )
            if course is None:
                raise PaymentOrderCourseNotFoundError("The course does not exist or access is denied.")

            order = PaymentOrder(
                order_no=_new_order_no(),
                user_id=int(user_id),
                course_id=course.id,
                product_code=product.product_code,
                product_snapshot=product.snapshot(),
                amount_cents=product.amount_cents,
                currency=product.currency,
                status="pending",
                request_key=normalized_request_key,
            )
            session.add(order)
            session.flush()
            return order
    except IntegrityError:
        with get_db_session() as session:
            existing = session.scalar(
                select(PaymentOrder).where(
                    PaymentOrder.user_id == int(user_id),
                    PaymentOrder.request_key == normalized_request_key,
                )
            )
            if existing is not None:
                return existing
        raise


def get_payment_order_for_user(order_no, user_id):
    with get_db_session() as session:
        return session.scalar(
            select(PaymentOrder).where(
                PaymentOrder.order_no == str(order_no),
                PaymentOrder.user_id == int(user_id),
            )
        )


def activate_payment_order(order_no, operator_note=None, now=None):
    current = _as_utc(now or datetime.now(timezone.utc))
    normalized_operator_note = str(operator_note).strip() or None if operator_note is not None else None
    with get_db_session() as session:
        order = session.scalar(
            select(PaymentOrder)
            .where(PaymentOrder.order_no == str(order_no))
            .with_for_update()
        )
        if order is None:
            raise PaymentOrderNotFoundError("The payment order does not exist.")
        if order.status == "paid":
            return _require_order_entitlement(session, order)
        if order.status != "pending":
            raise PaymentOrderStateError("Only pending payment orders can be activated.")

        claimed = session.execute(
            update(PaymentOrder)
            .where(PaymentOrder.id == order.id, PaymentOrder.status == "pending")
            .values(status="paid", paid_at=current)
        )
        if claimed.rowcount != 1:
            session.expire_all()
            stored = session.get(PaymentOrder, order.id)
            if stored is not None and stored.status == "paid":
                return _require_order_entitlement(session, stored)
            raise PaymentOrderStateError("The payment order could not be activated.")

        snapshot = dict(order.product_snapshot or {})
        _validate_product_snapshot(snapshot)
        entitlement = CourseEntitlement(
            user_id=order.user_id,
            course_id=order.course_id,
            product_code=str(snapshot["product_code"]),
            amount_cents=int(snapshot["amount_cents"]),
            payment_reference=f"order:{order.order_no}",
            status="active",
            activated_at=current,
            expires_at=_resolve_expiration(snapshot, current),
            follow_remaining=int(snapshot["follow_allowance"]),
            textbook_remaining=int(snapshot["textbook_allowance"]),
            exam_remaining=int(snapshot["exam_allowance"]),
            assistant_remaining=int(snapshot["assistant_allowance"]),
            operator_note=normalized_operator_note,
        )
        session.add(entitlement)
        session.flush()
        order.entitlement_id = entitlement.id
        order.operator_note = entitlement.operator_note
        order.status = "paid"
        order.paid_at = current
        session.flush()
        return entitlement


def _require_order_entitlement(session, order):
    if order.entitlement_id is None:
        raise PaymentOrderStateError("The paid order does not have an entitlement.")
    entitlement = session.get(CourseEntitlement, order.entitlement_id)
    if entitlement is None:
        raise PaymentOrderStateError("The activated entitlement no longer exists.")
    return entitlement


def _validate_product_snapshot(snapshot):
    required = {
        "product_code",
        "amount_cents",
        "currency",
        "duration_policy",
        "follow_allowance",
        "textbook_allowance",
        "exam_allowance",
        "assistant_allowance",
    }
    if not required.issubset(snapshot):
        raise PaymentOrderStateError("The payment order product snapshot is incomplete.")


def _resolve_expiration(snapshot, current):
    if snapshot["duration_policy"] != "semester_end":
        raise PaymentOrderStateError("The product duration policy is not supported.")
    minimum_expiration = current + timedelta(days=30)
    for year in range(current.year, current.year + 3):
        for month, day in ((1, 31), (7, 31)):
            candidate = datetime(year, month, day, 23, 59, 59, tzinfo=timezone.utc)
            if candidate >= minimum_expiration:
                return candidate
    raise PaymentOrderStateError("The entitlement expiration could not be resolved.")


def _new_order_no():
    return f"LO-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:12].upper()}"


def _as_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

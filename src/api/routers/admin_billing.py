from typing import Literal

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import require_admin_user
from src.api.schemas import (
    AdminPaymentOrderActionRequest,
    AdminPaymentOrderListResponse,
    AdminPaymentOrderResponse,
)
from src.services.payment_order_service import (
    PaymentOrderNotFoundError,
    PaymentOrderStateError,
    activate_payment_order,
    cancel_payment_order,
    get_payment_order,
    list_payment_orders,
)


router = APIRouter(prefix="/api/admin/billing", tags=["admin-billing"])


@router.get("/orders", response_model=AdminPaymentOrderListResponse)
def get_admin_payment_orders(
    status: Literal["pending", "paid", "cancelled"] | None = None,
    admin=Depends(require_admin_user),
):
    del admin
    return AdminPaymentOrderListResponse(
        orders=[_serialize_admin_payment_order(order) for order in list_payment_orders(status)]
    )


@router.get("/orders/{order_no}", response_model=AdminPaymentOrderResponse)
def get_admin_payment_order(order_no: str, admin=Depends(require_admin_user)):
    del admin
    order = get_payment_order(order_no)
    if order is None:
        raise _not_found()
    return _serialize_admin_payment_order(order)


@router.post("/orders/{order_no}/activate", response_model=AdminPaymentOrderResponse)
def activate_admin_payment_order(
    order_no: str,
    payload: AdminPaymentOrderActionRequest,
    admin=Depends(require_admin_user),
):
    operator_note = _operator_note(admin.id, "activated", payload.operator_note)
    try:
        activate_payment_order(order_no, operator_note=operator_note)
    except PaymentOrderNotFoundError as exc:
        raise _not_found() from exc
    except PaymentOrderStateError as exc:
        raise HTTPException(
            409,
            detail={"code": "payment_order_state_invalid", "message": str(exc)},
        ) from exc
    return _require_order(order_no)


@router.post("/orders/{order_no}/cancel", response_model=AdminPaymentOrderResponse)
def cancel_admin_payment_order(
    order_no: str,
    payload: AdminPaymentOrderActionRequest,
    admin=Depends(require_admin_user),
):
    operator_note = _operator_note(admin.id, "cancelled", payload.operator_note)
    try:
        cancel_payment_order(order_no, operator_note=operator_note)
    except PaymentOrderNotFoundError as exc:
        raise _not_found() from exc
    except PaymentOrderStateError as exc:
        raise HTTPException(
            409,
            detail={"code": "payment_order_state_invalid", "message": str(exc)},
        ) from exc
    return _require_order(order_no)


def _require_order(order_no):
    order = get_payment_order(order_no)
    if order is None:
        raise _not_found()
    return _serialize_admin_payment_order(order)


def _serialize_admin_payment_order(order):
    snapshot = dict(order.product_snapshot or {})
    return AdminPaymentOrderResponse(
        order_no=order.order_no,
        user_id=order.user_id,
        user_email=order.user.email,
        course_id=order.course_id,
        course_name=order.course.name,
        product_code=order.product_code,
        product_name=str(snapshot.get("name") or order.product_code),
        product_snapshot=snapshot,
        amount_cents=order.amount_cents,
        currency=order.currency,
        status=order.status,
        entitlement_id=order.entitlement_id,
        created_at=order.created_at,
        paid_at=order.paid_at,
        operator_note=order.operator_note,
    )


def _operator_note(operator_id, action, note):
    prefix = f"action={action} operator_id={int(operator_id)}"
    normalized_note = str(note).strip() if note is not None else ""
    return f"{prefix}: {normalized_note}" if normalized_note else prefix


def _not_found():
    return HTTPException(
        404,
        detail={"code": "payment_order_not_found", "message": "The payment order was not found."},
    )

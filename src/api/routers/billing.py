from fastapi import APIRouter, Depends, HTTPException, status

from src.billing.product_catalog import list_billing_products
from src.api.dependencies import require_current_user
from src.api.schemas import (
    AiGenerationUsageResponse,
    BillingProductListResponse,
    BillingProductResponse,
    CourseEntitlementResponse,
    PaymentOrderCreateRequest,
    PaymentOrderResponse,
    UsageSummaryResponse,
)
from src.services.quota_service import get_ai_generation_quota
from src.services.entitlement_service import list_entitlements
from src.services.payment_order_service import (
    BillingProductInactiveError,
    BillingProductNotFoundError,
    PaymentOrderCourseNotFoundError,
    create_payment_order,
    get_payment_order_for_user,
)


router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/products", response_model=BillingProductListResponse)
def get_billing_products(user=Depends(require_current_user)):
    del user
    return BillingProductListResponse(
        products=[BillingProductResponse(**product.snapshot()) for product in list_billing_products()]
    )


@router.post("/orders", response_model=PaymentOrderResponse, status_code=status.HTTP_201_CREATED)
def create_billing_order(payload: PaymentOrderCreateRequest, user=Depends(require_current_user)):
    try:
        order = create_payment_order(
            user.id,
            payload.course_id,
            payload.product_code,
            payload.request_key,
        )
    except BillingProductNotFoundError as exc:
        raise HTTPException(404, detail={"code": "billing_product_not_found", "message": str(exc)}) from exc
    except BillingProductInactiveError as exc:
        raise HTTPException(409, detail={"code": "billing_product_inactive", "message": str(exc)}) from exc
    except PaymentOrderCourseNotFoundError as exc:
        raise HTTPException(404, detail={"code": "course_not_found", "message": str(exc)}) from exc
    return _serialize_payment_order(order)


@router.get("/orders/{order_no}", response_model=PaymentOrderResponse)
def get_billing_order(order_no: str, user=Depends(require_current_user)):
    order = get_payment_order_for_user(order_no, user.id)
    if order is None:
        raise HTTPException(404, detail={"code": "payment_order_not_found", "message": "The payment order was not found."})
    return _serialize_payment_order(order)


@router.get("/usage", response_model=UsageSummaryResponse)
def get_usage_summary(user=Depends(require_current_user)):
    quota = get_ai_generation_quota(user.id)
    entitlements = list_entitlements(user.id)
    return UsageSummaryResponse(
        plan="free",
        ai_generations=AiGenerationUsageResponse(**quota),
        course_entitlements=[CourseEntitlementResponse(id=item.id, course_id=item.course_id, course_name=item.course.name, product_code=item.product_code, amount_cents=item.amount_cents, status=item.status, activated_at=item.activated_at, expires_at=item.expires_at, follow_remaining=item.follow_remaining, textbook_remaining=item.textbook_remaining, exam_remaining=item.exam_remaining, assistant_remaining=item.assistant_remaining) for item in entitlements],
    )


def _serialize_payment_order(order):
    return PaymentOrderResponse(
        order_no=order.order_no,
        user_id=order.user_id,
        course_id=order.course_id,
        product_code=order.product_code,
        product_snapshot=order.product_snapshot,
        amount_cents=order.amount_cents,
        currency=order.currency,
        status=order.status,
        entitlement_id=order.entitlement_id,
        created_at=order.created_at,
        paid_at=order.paid_at,
        operator_note=order.operator_note,
    )

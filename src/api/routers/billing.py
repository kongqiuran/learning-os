from fastapi import APIRouter, Depends

from src.api.dependencies import require_current_user
from src.api.schemas import AiGenerationUsageResponse, CourseEntitlementResponse, UsageSummaryResponse
from src.services.quota_service import get_ai_generation_quota
from src.services.entitlement_service import list_entitlements


router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/usage", response_model=UsageSummaryResponse)
def get_usage_summary(user=Depends(require_current_user)):
    quota = get_ai_generation_quota(user.id)
    entitlements = list_entitlements(user.id)
    return UsageSummaryResponse(
        plan="free",
        ai_generations=AiGenerationUsageResponse(**quota),
        course_entitlements=[CourseEntitlementResponse(id=item.id, course_id=item.course_id, course_name=item.course.name, product_code=item.product_code, amount_cents=item.amount_cents, status=item.status, activated_at=item.activated_at, expires_at=item.expires_at, follow_remaining=item.follow_remaining, textbook_remaining=item.textbook_remaining, exam_remaining=item.exam_remaining, assistant_remaining=item.assistant_remaining) for item in entitlements],
    )

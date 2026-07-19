from fastapi import APIRouter, Depends

from src.api.dependencies import require_current_user
from src.api.schemas import AiGenerationUsageResponse, UsageSummaryResponse
from src.services.quota_service import get_ai_generation_quota


router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/usage", response_model=UsageSummaryResponse)
def get_usage_summary(user=Depends(require_current_user)):
    quota = get_ai_generation_quota(user.id)
    return UsageSummaryResponse(
        plan="free",
        ai_generations=AiGenerationUsageResponse(**quota),
    )

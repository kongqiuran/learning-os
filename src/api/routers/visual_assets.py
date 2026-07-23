from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import require_current_user
from src.api.schemas import VisualAssetListResponse, VisualGenerationResponse
from src.api.serializers import serialize_visual_asset
from src.visual.service import VisualService
from src.visual.target_resolver import VisualTargetNotFoundError


router = APIRouter(prefix="/api/visual-assets", tags=["visual-assets"])


@router.get(
    "/{target_type}/{target_id}",
    response_model=VisualAssetListResponse,
)
def get_visual_assets(
    target_type: str,
    target_id: str,
    user=Depends(require_current_user),
):
    try:
        assets = VisualService().list_current(target_type, target_id, user.id)
    except VisualTargetNotFoundError:
        raise _target_not_found()
    return VisualAssetListResponse(
        target_type=target_type,
        target_id=target_id,
        items=[serialize_visual_asset(asset) for asset in assets],
    )


@router.post(
    "/{target_type}/{target_id}",
    response_model=VisualGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_visual_asset(
    target_type: str,
    target_id: str,
    user=Depends(require_current_user),
):
    try:
        asset, plan = VisualService().request_generation(
            target_type,
            target_id,
            user.id,
        )
    except VisualTargetNotFoundError:
        raise _target_not_found()
    return VisualGenerationResponse(
        recommended=plan.need_visual,
        reason=plan.reason,
        confidence=plan.confidence,
        asset=serialize_visual_asset(asset) if asset is not None else None,
    )


def _target_not_found():
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "visual_target_not_found",
            "message": "The visual target was not found.",
        },
    )

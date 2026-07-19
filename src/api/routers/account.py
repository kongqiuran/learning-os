from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.dependencies import require_current_user
from src.api.schemas import AccountDeletionRequest, AccountDeletionResponse
from src.services.account_deletion_service import (
    AccountDeletionAuthenticationError,
    AccountDeletionConfirmationError,
    AccountDeletionService,
)


router = APIRouter(prefix="/api/account", tags=["account"])


@router.delete("", response_model=AccountDeletionResponse)
def delete_account(
    payload: AccountDeletionRequest,
    request: Request,
    user=Depends(require_current_user),
):
    service = AccountDeletionService()
    try:
        result = service.delete_current_user(
            user.id,
            payload.password,
            payload.confirmation,
        )
    except AccountDeletionAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": str(exc)},
        ) from exc
    except AccountDeletionConfirmationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "confirmation_required", "message": str(exc)},
        ) from exc

    request.session.clear()
    return AccountDeletionResponse(
        deletion_id=result.deletion_id,
        status="deleted",
        message="The account and its data were permanently deleted.",
    )

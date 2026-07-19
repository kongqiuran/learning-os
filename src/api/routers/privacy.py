from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import require_current_user
from src.api.schemas import (
    PrivacyConsentRequest,
    PrivacyConsentResponse,
    PrivacyConsentStatusResponse,
    PrivacyPolicyCurrentResponse,
)
from src.services.privacy_consent_service import PrivacyConsentService


router = APIRouter(prefix="/api/privacy", tags=["privacy"])
privacy_consent_service = PrivacyConsentService()


@router.get("/current", response_model=PrivacyPolicyCurrentResponse)
def get_current_privacy_policy():
    return PrivacyPolicyCurrentResponse(
        policy_version=privacy_consent_service.get_current_policy_version()
    )


@router.get("/status", response_model=PrivacyConsentStatusResponse)
def get_privacy_consent_status(user=Depends(require_current_user)):
    status_result = privacy_consent_service.get_status(user.id)
    return PrivacyConsentStatusResponse(
        current_version=status_result.current_version,
        accepted=status_result.accepted,
        requires_reconsent=status_result.requires_reconsent,
    )


@router.post("/consent", response_model=PrivacyConsentResponse)
def submit_privacy_consent(
    payload: PrivacyConsentRequest,
    user=Depends(require_current_user),
):
    if not payload.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "privacy_consent_required",
                "message": "Privacy consent must be explicitly accepted.",
            },
        )

    consent, created = privacy_consent_service.record_current_consent(user.id)
    return PrivacyConsentResponse(
        policy_version=consent.policy_version,
        accepted_at=_as_utc(consent.accepted_at),
        created=created,
    )


def _as_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

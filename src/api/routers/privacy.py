from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import require_current_user
from src.api.schemas import (
    PrivacyConsentRequest,
    PrivacyConsentResponse,
    PrivacyPolicyCurrentResponse,
)
from src.services.privacy_consent_service import (
    get_current_policy_version,
    record_privacy_consent,
)


router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.get("/current", response_model=PrivacyPolicyCurrentResponse)
def get_current_privacy_policy():
    return PrivacyPolicyCurrentResponse(policy_version=get_current_policy_version())


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

    current_version = get_current_policy_version()
    if payload.policy_version != current_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "policy_version_outdated",
                "message": "Review and accept the current privacy policy version.",
            },
        )

    consent, created = record_privacy_consent(user.id, current_version)
    return PrivacyConsentResponse(
        policy_version=consent.policy_version,
        accepted_at=_as_utc(consent.accepted_at),
        created=created,
    )


def _as_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

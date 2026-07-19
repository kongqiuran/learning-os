import os

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.database import get_db_session
from src.models import PrivacyConsent


DEFAULT_PRIVACY_POLICY_VERSION = "2026.07.01-v1"


def get_current_policy_version():
    configured = os.getenv("PRIVACY_POLICY_VERSION", DEFAULT_PRIVACY_POLICY_VERSION)
    return configured.strip() or DEFAULT_PRIVACY_POLICY_VERSION


def record_privacy_consent(user_id, policy_version):
    normalized_version = str(policy_version).strip()
    if user_id is None or not normalized_version:
        raise ValueError("A user and policy version are required.")

    try:
        with get_db_session() as session:
            existing = session.scalar(
                select(PrivacyConsent).where(
                    PrivacyConsent.user_id == int(user_id),
                    PrivacyConsent.policy_version == normalized_version,
                )
            )
            if existing is not None:
                return existing, False

            consent = PrivacyConsent(
                user_id=int(user_id),
                policy_version=normalized_version,
            )
            session.add(consent)
            session.flush()
            return consent, True
    except IntegrityError:
        with get_db_session() as session:
            existing = session.scalar(
                select(PrivacyConsent).where(
                    PrivacyConsent.user_id == int(user_id),
                    PrivacyConsent.policy_version == normalized_version,
                )
            )
            if existing is None:
                raise
            return existing, False

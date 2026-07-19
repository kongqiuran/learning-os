from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src import config
from src.database import get_db_session
from src.models import PrivacyConsent


@dataclass(frozen=True)
class PrivacyConsentStatus:
    current_version: str
    accepted: bool
    requires_reconsent: bool


class PrivacyConsentService:
    @staticmethod
    def get_current_policy_version():
        return config.CURRENT_PRIVACY_POLICY_VERSION

    @staticmethod
    def get_latest_consent(user_id):
        if user_id is None:
            raise ValueError("A user is required.")

        with get_db_session() as session:
            return session.scalar(
                select(PrivacyConsent)
                .where(PrivacyConsent.user_id == int(user_id))
                .order_by(PrivacyConsent.accepted_at.desc(), PrivacyConsent.id.desc())
                .limit(1)
            )

    def get_status(self, user_id):
        if user_id is None:
            raise ValueError("A user is required.")

        current_version = self.get_current_policy_version()
        with get_db_session() as session:
            current_consent = session.scalar(
                select(PrivacyConsent).where(
                    PrivacyConsent.user_id == int(user_id),
                    PrivacyConsent.policy_version == current_version,
                )
            )

        accepted = current_consent is not None
        return PrivacyConsentStatus(
            current_version=current_version,
            accepted=accepted,
            requires_reconsent=not accepted,
        )

    def record_current_consent(self, user_id):
        if user_id is None:
            raise ValueError("A user is required.")

        current_version = self.get_current_policy_version()

        try:
            with get_db_session() as session:
                existing = session.scalar(
                    select(PrivacyConsent).where(
                        PrivacyConsent.user_id == int(user_id),
                        PrivacyConsent.policy_version == current_version,
                    )
                )
                if existing is not None:
                    return existing, False

                consent = PrivacyConsent(
                    user_id=int(user_id),
                    policy_version=current_version,
                )
                session.add(consent)
                session.flush()
                return consent, True
        except IntegrityError:
            with get_db_session() as session:
                existing = session.scalar(
                    select(PrivacyConsent).where(
                        PrivacyConsent.user_id == int(user_id),
                        PrivacyConsent.policy_version == current_version,
                    )
                )
                if existing is None:
                    raise
                return existing, False

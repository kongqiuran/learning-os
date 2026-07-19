import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from src.api.factory import create_app
from src.database import create_database_tables, get_db_session
from src.models import PrivacyConsent, User
from src.services.user_service import register_user


class PrivacyConsentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    def setUp(self):
        with get_db_session() as session:
            session.query(PrivacyConsent).delete()
            session.query(User).delete()

        self.user = register_user("privacy@example.com", "privacy-password")
        self.client = TestClient(create_app(session_secret="privacy-consent-test-secret"))
        login_response = self.client.post(
            "/api/auth/login",
            json={
                "email": "privacy@example.com",
                "password": "privacy-password",
            },
        )
        self.assertEqual(login_response.status_code, 200)

    def tearDown(self):
        self.client.close()

    def test_user_accepts_current_privacy_policy(self):
        with patch.dict(os.environ, {"PRIVACY_POLICY_VERSION": "2026.07-v1"}):
            current_response = self.client.get("/api/privacy/current")
            consent_response = self.client.post(
                "/api/privacy/consent",
                json={"policy_version": "2026.07-v1", "accepted": True},
            )

        self.assertEqual(current_response.status_code, 200)
        self.assertEqual(current_response.json()["policy_version"], "2026.07-v1")
        self.assertEqual(consent_response.status_code, 200)
        self.assertTrue(consent_response.json()["created"])
        with get_db_session() as session:
            consent = session.scalar(
                select(PrivacyConsent).where(PrivacyConsent.user_id == self.user.id)
            )
            self.assertEqual(consent.policy_version, "2026.07-v1")
            self.assertIsNotNone(consent.accepted_at)

    def test_duplicate_consent_is_idempotent(self):
        payload = {"policy_version": "2026.07-v1", "accepted": True}
        with patch.dict(os.environ, {"PRIVACY_POLICY_VERSION": "2026.07-v1"}):
            first_response = self.client.post("/api/privacy/consent", json=payload)
            second_response = self.client.post("/api/privacy/consent", json=payload)

        self.assertTrue(first_response.json()["created"])
        self.assertFalse(second_response.json()["created"])
        self.assertEqual(
            first_response.json()["accepted_at"],
            second_response.json()["accepted_at"],
        )
        with get_db_session() as session:
            consent_count = session.scalar(
                select(func.count(PrivacyConsent.id)).where(
                    PrivacyConsent.user_id == self.user.id
                )
            )
            self.assertEqual(consent_count, 1)

    def test_new_policy_version_creates_new_consent_record(self):
        with patch.dict(os.environ, {"PRIVACY_POLICY_VERSION": "2026.07-v1"}):
            first_response = self.client.post(
                "/api/privacy/consent",
                json={"policy_version": "2026.07-v1", "accepted": True},
            )
        with patch.dict(os.environ, {"PRIVACY_POLICY_VERSION": "2026.08-v2"}):
            current_response = self.client.get("/api/privacy/current")
            second_response = self.client.post(
                "/api/privacy/consent",
                json={"policy_version": "2026.08-v2", "accepted": True},
            )

        self.assertTrue(first_response.json()["created"])
        self.assertEqual(current_response.json()["policy_version"], "2026.08-v2")
        self.assertTrue(second_response.json()["created"])
        with get_db_session() as session:
            versions = set(
                session.scalars(
                    select(PrivacyConsent.policy_version).where(
                        PrivacyConsent.user_id == self.user.id
                    )
                )
            )
            self.assertEqual(versions, {"2026.07-v1", "2026.08-v2"})


if __name__ == "__main__":
    unittest.main()

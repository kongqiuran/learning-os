import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from src import config
from src.api.factory import create_app
from src.database import create_database_tables, get_db_session
from src.models import PrivacyConsent, User
from src.services.user_service import register_user


CURRENT_VERSION = "2026.07.01-v1"
NEXT_VERSION = "2026.08.01-v2"


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
        self._login(self.client, "privacy@example.com", "privacy-password")
        self.version_patch = patch.object(
            config,
            "CURRENT_PRIVACY_POLICY_VERSION",
            CURRENT_VERSION,
        )
        self.version_patch.start()

    def tearDown(self):
        self.version_patch.stop()
        self.client.close()

    def test_new_user_requires_reconsent(self):
        response = self.client.get("/api/privacy/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "current_version": CURRENT_VERSION,
                "accepted": False,
                "requires_reconsent": True,
            },
        )

    def test_user_accepts_server_selected_current_version(self):
        consent_response = self.client.post(
            "/api/privacy/consent",
            json={"accepted": True},
        )
        status_response = self.client.get("/api/privacy/status")

        self.assertEqual(consent_response.status_code, 200)
        self.assertEqual(consent_response.json()["policy_version"], CURRENT_VERSION)
        self.assertTrue(consent_response.json()["created"])
        self.assertEqual(
            status_response.json(),
            {
                "current_version": CURRENT_VERSION,
                "accepted": True,
                "requires_reconsent": False,
            },
        )
        with get_db_session() as session:
            consent = session.scalar(
                select(PrivacyConsent).where(PrivacyConsent.user_id == self.user.id)
            )
            self.assertEqual(consent.policy_version, CURRENT_VERSION)
            self.assertIsNotNone(consent.accepted_at)

    def test_old_consent_requires_reconsent_after_version_upgrade(self):
        self.client.post("/api/privacy/consent", json={"accepted": True})

        with patch.object(config, "CURRENT_PRIVACY_POLICY_VERSION", NEXT_VERSION):
            response = self.client.get("/api/privacy/status")

        self.assertEqual(
            response.json(),
            {
                "current_version": NEXT_VERSION,
                "accepted": False,
                "requires_reconsent": True,
            },
        )

    def test_reconsent_for_new_version_restores_accepted_status(self):
        self.client.post("/api/privacy/consent", json={"accepted": True})

        with patch.object(config, "CURRENT_PRIVACY_POLICY_VERSION", NEXT_VERSION):
            before_response = self.client.get("/api/privacy/status")
            consent_response = self.client.post(
                "/api/privacy/consent",
                json={"accepted": True},
            )
            after_response = self.client.get("/api/privacy/status")

        self.assertTrue(before_response.json()["requires_reconsent"])
        self.assertEqual(consent_response.json()["policy_version"], NEXT_VERSION)
        self.assertEqual(
            after_response.json(),
            {
                "current_version": NEXT_VERSION,
                "accepted": True,
                "requires_reconsent": False,
            },
        )
        with get_db_session() as session:
            versions = set(
                session.scalars(
                    select(PrivacyConsent.policy_version).where(
                        PrivacyConsent.user_id == self.user.id
                    )
                )
            )
            self.assertEqual(versions, {CURRENT_VERSION, NEXT_VERSION})

    def test_client_cannot_submit_an_arbitrary_policy_version(self):
        response = self.client.post(
            "/api/privacy/consent",
            json={"accepted": True, "policy_version": "forged-old-version"},
        )

        self.assertEqual(response.status_code, 422)
        with get_db_session() as session:
            self.assertEqual(session.scalar(select(func.count(PrivacyConsent.id))), 0)

    def test_duplicate_consent_is_idempotent(self):
        first_response = self.client.post(
            "/api/privacy/consent",
            json={"accepted": True},
        )
        second_response = self.client.post(
            "/api/privacy/consent",
            json={"accepted": True},
        )

        self.assertTrue(first_response.json()["created"])
        self.assertFalse(second_response.json()["created"])
        self.assertEqual(
            first_response.json()["accepted_at"],
            second_response.json()["accepted_at"],
        )

    def test_consent_status_and_updates_are_isolated_by_session_user(self):
        user_b = register_user("privacy-b@example.com", "privacy-b-password")
        client_b = TestClient(create_app(session_secret="privacy-consent-test-secret"))
        self.addCleanup(client_b.close)
        self._login(client_b, "privacy-b@example.com", "privacy-b-password")
        client_b.post("/api/privacy/consent", json={"accepted": True})

        user_a_status = self.client.get(
            f"/api/privacy/status?user_id={user_b.id}"
        )
        forged_update = self.client.post(
            "/api/privacy/consent",
            json={"accepted": True, "user_id": user_b.id},
        )

        self.assertFalse(user_a_status.json()["accepted"])
        self.assertTrue(user_a_status.json()["requires_reconsent"])
        self.assertEqual(forged_update.status_code, 422)
        with get_db_session() as session:
            b_consents = session.scalar(
                select(func.count(PrivacyConsent.id)).where(
                    PrivacyConsent.user_id == user_b.id
                )
            )
            a_consents = session.scalar(
                select(func.count(PrivacyConsent.id)).where(
                    PrivacyConsent.user_id == self.user.id
                )
            )
            self.assertEqual(b_consents, 1)
            self.assertEqual(a_consents, 0)

    @staticmethod
    def _login(client, email, password):
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        if response.status_code != 200:
            raise AssertionError(response.text)


if __name__ == "__main__":
    unittest.main()

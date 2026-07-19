import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.factory import create_app
from src.services.user_service import UserAlreadyExistsError


def fake_user(email="student@example.com"):
    return SimpleNamespace(
        id=1,
        email=email,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class ApiAuthenticationTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(session_secret="test-session-secret"))

    def tearDown(self):
        self.client.close()

    def test_health_endpoint_is_public(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_login_sets_session_and_me_restores_user(self):
        user = fake_user()
        with patch("src.api.routers.auth.authenticate_user", return_value=user):
            response = self.client.post(
                "/api/auth/login",
                json={"email": user.email, "password": "secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["email"], user.email)
        self.assertIn("learning_os_session", self.client.cookies)

        with patch("src.api.dependencies.get_user_by_email", return_value=user):
            response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["id"], 1)

    def test_invalid_login_returns_consistent_error(self):
        with patch("src.api.routers.auth.authenticate_user", return_value=None):
            response = self.client.post(
                "/api/auth/login",
                json={"email": "student@example.com", "password": "wrong"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "invalid_credentials")

    def test_registration_starts_session(self):
        user = fake_user("new@example.com")
        with patch("src.api.routers.auth.register_user", return_value=user):
            response = self.client.post(
                "/api/auth/register",
                json={
                    "email": user.email,
                    "password": "secret12",
                    "confirm_password": "secret12",
                    "accepted_terms": True,
                },
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["email"], user.email)

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "password": "secret",
                "confirm_password": "different",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "password_mismatch")

    def test_registration_maps_existing_user_error(self):
        with patch(
            "src.api.routers.auth.register_user",
            side_effect=UserAlreadyExistsError("already registered"),
        ):
            response = self.client.post(
                "/api/auth/register",
                json={
                    "email": "existing@example.com",
                    "password": "secret12",
                    "confirm_password": "secret12",
                    "accepted_terms": True,
                },
            )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "email_registered")

    def test_registration_requires_terms_consent(self):
        response = self.client.post(
            "/api/auth/register",
            json={"email": "terms@example.com", "password": "password", "confirm_password": "password"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "terms_consent_required")

    def test_registration_rejects_short_password(self):
        response = self.client.post(
            "/api/auth/register",
            json={"email": "weak@example.com", "password": "short", "confirm_password": "short", "accepted_terms": True},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "weak_password")

    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_logout_clears_session(self):
        user = fake_user()
        with patch("src.api.routers.auth.authenticate_user", return_value=user):
            self.client.post(
                "/api/auth/login",
                json={"email": user.email, "password": "secret"},
            )
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("learning_os_session", self.client.cookies)


if __name__ == "__main__":
    unittest.main()

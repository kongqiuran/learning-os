import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.factory import create_app


NOW = datetime(2026, 7, 15, tzinfo=timezone.utc)


def fake_user(user_id=1):
    return SimpleNamespace(id=user_id, email=f"student{user_id}@example.com", created_at=NOW)


def fake_course(course_id=10, user_id=1, name="Signals and Systems"):
    return SimpleNamespace(
        id=course_id,
        user_id=user_id,
        name=name,
        description="Core engineering course",
        created_at=NOW,
    )


def fake_document(document_id=20, course_id=10, user_id=1):
    return SimpleNamespace(
        id=document_id,
        course_id=course_id,
        user_id=user_id,
        uploaded_at=NOW + timedelta(days=1),
    )


class CourseApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(session_secret="test-session-secret"))
        self.user = fake_user()
        self.auth_patch = patch("src.api.dependencies.get_user_by_email", return_value=self.user)
        self.auth_patch.start()
        with self.client as client:
            with patch("src.api.routers.auth.authenticate_user", return_value=self.user):
                client.post(
                    "/api/auth/login",
                    json={"email": self.user.email, "password": "secret"},
                )

    def tearDown(self):
        self.auth_patch.stop()
        self.client.close()

    def test_dashboard_uses_authenticated_user_and_real_counts(self):
        course = fake_course()
        document = fake_document()
        package = SimpleNamespace(created_at=NOW + timedelta(days=2))
        with (
            patch("src.api.routers.courses.list_courses_for_user", return_value=[course]) as list_courses,
            patch("src.api.routers.courses.list_documents_for_course", return_value=[document]) as list_documents,
            patch("src.api.routers.courses.get_learning_package", return_value=package),
        ):
            response = self.client.get("/api/dashboard")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["course_count"], 1)
        self.assertEqual(payload["document_count"], 1)
        serialized_updated_at = datetime.fromisoformat(
            payload["courses"][0]["updated_at"].replace("Z", "+00:00")
        )
        self.assertEqual(serialized_updated_at, package.created_at)
        list_courses.assert_called_once_with(self.user.id)
        list_documents.assert_called_once_with(self.user.id, course.id)

    def test_create_course_delegates_to_existing_service(self):
        course = fake_course(name="Semiconductor Physics")
        with patch("src.api.routers.courses.create_course", return_value=course) as create:
            response = self.client.post(
                "/api/courses",
                json={"name": course.name, "description": course.description},
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], course.name)
        create.assert_called_once_with(self.user.id, course.name, course.description)

    def test_get_course_returns_not_found_for_other_users_course(self):
        with patch("src.api.routers.courses.get_course_for_user", return_value=None) as get_course:
            response = self.client.get("/api/courses/99")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "course_not_found")
        get_course.assert_called_once_with(99, self.user.id)

    def test_delete_course_uses_owner_scoped_service(self):
        with patch("src.api.routers.courses.delete_course_for_user", return_value=True) as delete:
            response = self.client.delete("/api/courses/10")
        self.assertEqual(response.status_code, 200)
        delete.assert_called_once_with(10, self.user.id)

    def test_delete_course_hides_unauthorized_course(self):
        with patch("src.api.routers.courses.delete_course_for_user", return_value=False):
            response = self.client.delete("/api/courses/99")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()

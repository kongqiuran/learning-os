import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.adapters.assistant_adapter import AssistantAnswer
from src.api.factory import create_app


NOW = datetime(2026, 7, 15, tzinfo=timezone.utc)


def fake_user(user_id=1):
    return SimpleNamespace(id=user_id, email=f"student{user_id}@example.com", created_at=NOW)


def fake_course(course_id=10, user_id=1):
    return SimpleNamespace(
        id=course_id,
        user_id=user_id,
        name="Signals and Systems",
        description="Core engineering course",
        created_at=NOW,
    )


def fake_document(document_id=20, course_id=10, user_id=1):
    return SimpleNamespace(
        id=document_id,
        course_id=course_id,
        user_id=user_id,
        original_filename="lecture.md",
        mime_type="text/markdown",
        file_size=128,
        processing_status="uploaded",
        document_type="NOTES",
        uploaded_at=NOW,
    )


def fake_package(status="completed"):
    return SimpleNamespace(
        id=30,
        status=status,
        version=1,
        content_json={"key_points": ["Fourier transform"]},
        created_at=NOW,
    )


class CourseSpaceApiTest(unittest.TestCase):
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

    def test_course_space_returns_real_documents_and_latest_package(self):
        course = fake_course()
        document = fake_document()
        package = fake_package()
        with (
            patch("src.api.routers.course_space.get_course_for_user", return_value=course),
            patch("src.api.routers.course_space.list_documents_for_course", return_value=[document]),
            patch("src.api.routers.course_space.get_learning_package", return_value=package),
        ):
            response = self.client.get("/api/courses/10/space")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["course"]["document_count"], 1)
        self.assertEqual(payload["documents"][0]["name"], "lecture.md")
        self.assertEqual(payload["learning_package"]["content"]["key_points"], ["Fourier transform"])

    def test_upload_adapts_fastapi_file_to_existing_service(self):
        course = fake_course()
        document = fake_document()
        with (
            patch("src.api.routers.course_space.get_course_for_user", return_value=course),
            patch("src.api.routers.course_space.save_uploaded_document", return_value=document) as save,
        ):
            response = self.client.post(
                "/api/courses/10/documents",
                files={"file": ("lecture.md", b"# Fourier", "text/markdown")},
                data={"document_type": "NOTES"},
            )

        self.assertEqual(response.status_code, 201)
        uploaded_file = save.call_args.args[2]
        self.assertEqual(uploaded_file.name, "lecture.md")
        self.assertEqual(uploaded_file.type, "text/markdown")
        self.assertEqual(uploaded_file.getvalue(), b"# Fourier")
        self.assertEqual(save.call_args.args[3], "NOTES")

    def test_upload_adapter_fills_missing_markdown_mime_type(self):
        document = fake_document()
        with (
            patch("src.api.routers.course_space.get_course_for_user", return_value=fake_course()),
            patch("src.api.routers.course_space.save_uploaded_document", return_value=document) as save,
        ):
            response = self.client.post(
                "/api/courses/10/documents",
                files={"file": ("lecture.md", b"# Fourier", "application/octet-stream")},
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(save.call_args.args[2].type, "text/markdown")

    def test_delete_document_uses_owner_scoped_service(self):
        with (
            patch("src.api.routers.course_space.get_course_for_user", return_value=fake_course()),
            patch("src.api.routers.course_space.delete_document_for_user", return_value=True) as delete,
        ):
            response = self.client.delete("/api/courses/10/documents/20")

        self.assertEqual(response.status_code, 200)
        delete.assert_called_once_with(20, self.user.id, 10)

    def test_generate_and_assistant_delegate_to_adapters(self):
        package = fake_package()
        with (
            patch("src.api.routers.course_space.get_course_for_user", return_value=fake_course()),
            patch("src.api.routers.course_space.generate_course_package", return_value=package) as generate,
            patch(
                "src.api.routers.course_space.answer_course_question",
                return_value=AssistantAnswer("根据课程资料解释。", ["lecture.md"]),
            ) as answer,
        ):
            generate_response = self.client.post("/api/courses/10/learning-package/generate")
            assistant_response = self.client.post(
                "/api/courses/10/assistant/query",
                json={"question": "Why?", "current_section": "重点内容"},
            )

        self.assertEqual(generate_response.status_code, 200)
        self.assertEqual(assistant_response.status_code, 200)
        generate.assert_called_once_with(10, self.user.id)
        answer.assert_called_once_with(10, self.user.id, "Why?", "重点内容")

    def test_other_users_course_is_hidden_from_every_course_space_action(self):
        requests = [
            ("get", "/api/courses/99/space", {}),
            (
                "post",
                "/api/courses/99/documents",
                {"files": {"file": ("note.txt", b"text", "text/plain")}},
            ),
            ("delete", "/api/courses/99/documents/20", {}),
            ("post", "/api/courses/99/learning-package/generate", {}),
            ("post", "/api/courses/99/assistant/query", {"json": {"question": "Why?"}}),
        ]
        with patch("src.api.routers.course_space.get_course_for_user", return_value=None):
            for method, path, kwargs in requests:
                with self.subTest(path=path):
                    response = getattr(self.client, method)(path, **kwargs)
                    self.assertEqual(response.status_code, 404)
                    self.assertEqual(response.json()["error"]["code"], "course_not_found")

    def test_assistant_rejects_blank_question(self):
        with patch("src.api.routers.course_space.get_course_for_user", return_value=fake_course()):
            response = self.client.post(
                "/api/courses/10/assistant/query",
                json={"question": "   "},
            )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "invalid_request")


if __name__ == "__main__":
    unittest.main()

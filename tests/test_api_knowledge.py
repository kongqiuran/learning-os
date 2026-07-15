import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.adapters.knowledge_adapter import KnowledgeItem
from src.api.factory import create_app


NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def fake_user(user_id=1):
    return SimpleNamespace(id=user_id, email=f"student{user_id}@example.com", created_at=NOW)


def fake_course(course_id=10, user_id=1):
    return SimpleNamespace(id=course_id, user_id=user_id, name="Signals")


def fake_knowledge():
    return KnowledgeItem(
        id="analysis-30-topic-0",
        title="Fourier transform",
        content="Frequency-domain representation.",
        importance=5,
        course_id=10,
        course_name="Signals",
        document_id=20,
        source_file="lecture.md",
        updated_at=NOW,
        viewed=False,
        viewed_at=None,
        core_explanation="Frequency-domain representation.",
        exam_value="Common calculation topic.",
        must_master=["Definition"],
        memory_tips="Compare time and frequency domains.",
        reason="Central concept.",
        source_formulas=[{"name": "Definition"}],
        source_errors=["Wrong shift direction"],
    )


class KnowledgeApiTest(unittest.TestCase):
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

    def test_course_knowledge_returns_mapped_items(self):
        item = fake_knowledge()
        with (
            patch("src.api.routers.knowledge.get_course_for_user", return_value=fake_course()),
            patch("src.api.routers.knowledge.list_course_knowledge", return_value=[item]),
        ):
            response = self.client.get("/api/courses/10/knowledge")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["knowledge_count"], 1)
        self.assertEqual(response.json()["items"][0]["source_file"], "lecture.md")

    def test_knowledge_detail_returns_existing_analysis_fields(self):
        with patch("src.api.routers.knowledge.get_knowledge_item", return_value=fake_knowledge()):
            response = self.client.get("/api/knowledge/analysis-30-topic-0")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["must_master"], ["Definition"])
        self.assertEqual(response.json()["source_errors"], ["Wrong shift direction"])

    def test_patch_viewed_returns_persisted_timestamp(self):
        with patch("src.api.routers.knowledge.mark_knowledge_viewed", return_value=NOW) as mark:
            response = self.client.patch("/api/knowledge/analysis-30-topic-0/viewed")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["viewed"])
        mark.assert_called_once_with("analysis-30-topic-0", self.user.id)

    def test_other_users_course_and_knowledge_are_hidden(self):
        with (
            patch("src.api.routers.knowledge.get_course_for_user", return_value=None),
            patch("src.api.routers.knowledge.get_knowledge_item", return_value=None),
            patch("src.api.routers.knowledge.mark_knowledge_viewed", return_value=None),
        ):
            responses = [
                self.client.get("/api/courses/99/knowledge"),
                self.client.get("/api/knowledge/analysis-99-topic-0"),
                self.client.patch("/api/knowledge/analysis-99-topic-0/viewed"),
            ]

        for response in responses:
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["error"]["code"], "knowledge_not_found")


if __name__ == "__main__":
    unittest.main()

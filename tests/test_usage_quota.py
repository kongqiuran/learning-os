import os
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.dependencies import require_current_user
from src.api.factory import create_app
from src.database import create_database_tables, get_db_session
from src.models import UsageRecord, User, UserPlan
from src.services.quota_service import (
    UsageQuotaExceededError,
    get_ai_generation_usage,
    reserve_ai_generation,
)
from src.services.user_service import register_user


NOW = datetime(2026, 7, 19, tzinfo=timezone.utc)


class UsageQuotaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    def setUp(self):
        with get_db_session() as session:
            session.query(UsageRecord).delete()
            session.query(UserPlan).delete()
            session.query(User).delete()

        self.user_a = register_user("quota-a@example.com", "password-a")
        self.user_b = register_user("quota-b@example.com", "password-b")
        self.app = create_app(session_secret="usage-quota-test-secret")
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()

    def test_free_user_usage_count_reaches_limit(self):
        with patch.dict(os.environ, {"FREE_MONTHLY_AI_GENERATIONS": "2"}):
            reserve_ai_generation(self.user_a.id, now=NOW)
            reserve_ai_generation(self.user_a.id, now=NOW)

        self.assertEqual(get_ai_generation_usage(self.user_a.id, now=NOW), 2)
        with get_db_session() as session:
            plan = session.query(UserPlan).filter_by(user_id=self.user_a.id).one()
            self.assertEqual(plan.plan_code, "free")
            self.assertEqual(plan.status, "active")

    def test_generation_is_rejected_before_task_creation_when_quota_is_exceeded(self):
        with patch.dict(os.environ, {"FREE_MONTHLY_AI_GENERATIONS": "2"}):
            reserve_ai_generation(self.user_a.id)
            reserve_ai_generation(self.user_a.id)
            self._authenticate_as(self.user_a)
            with (
                patch(
                    "src.api.routers.course_space.get_course_for_user",
                    return_value=SimpleNamespace(id=10, user_id=self.user_a.id),
                ),
                patch("src.api.routers.course_space.queue_course_package") as queue,
            ):
                response = self.client.post("/api/courses/10/learning-package/generate")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "quota_exceeded")
        self.assertEqual(response.json()["error"]["metric"], "ai_generation")
        self.assertEqual(response.json()["error"]["remaining"], 0)
        queue.assert_not_called()

    def test_different_users_have_isolated_quotas(self):
        with patch.dict(os.environ, {"FREE_MONTHLY_AI_GENERATIONS": "2"}):
            reserve_ai_generation(self.user_a.id, now=NOW)
            reserve_ai_generation(self.user_a.id, now=NOW)
            with self.assertRaises(UsageQuotaExceededError):
                reserve_ai_generation(self.user_a.id, now=NOW)

            reservation_b = reserve_ai_generation(self.user_b.id, now=NOW)

        self.assertEqual(reservation_b.user_id, self.user_b.id)
        self.assertEqual(get_ai_generation_usage(self.user_a.id, now=NOW), 2)
        self.assertEqual(get_ai_generation_usage(self.user_b.id, now=NOW), 1)

    def _authenticate_as(self, user):
        self.app.dependency_overrides[require_current_user] = lambda: user


if __name__ == "__main__":
    unittest.main()

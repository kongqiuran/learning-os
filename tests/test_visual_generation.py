import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

import worker
from src.api.factory import create_app
from src.database import create_database_tables, get_db_session
from src.models import (
    Course,
    Document,
    DocumentAnalysis,
    Task,
    User,
    VisualAsset,
)
from src.visual.generators.mermaid_generator import MermaidGenerator
from src.visual.generators.svg_generator import SvgGenerator
from src.visual.planner import VisualPlanner
from src.visual.service import VisualService, build_source_hash


def planner_snapshot(**updates):
    value = {
        "id": "analysis-1-topic-0",
        "title": "Fourier transform",
        "content": "A frequency-domain representation.",
        "importance": 3,
        "must_master": [],
        "core_explanation": "A frequency-domain representation.",
        "exam_value": "",
        "memory_tips": "",
        "reason": "",
        "source_formulas": [],
    }
    value.update(updates)
    return value


class VisualPlannerTest(unittest.TestCase):
    def test_high_importance_automatically_creates_plan(self):
        plan = VisualPlanner().plan(planner_snapshot(importance=4))

        self.assertTrue(plan.need_visual)
        self.assertEqual(plan.type, "diagram")
        self.assertEqual(plan.generator, "svg")
        self.assertGreater(plan.confidence, 0)

    def test_structural_complexity_triggers_without_high_importance(self):
        plan = VisualPlanner().plan(
            planner_snapshot(
                importance=2,
                content="结构包括分类、关系和完整流程。首先输入，然后变换，最后输出。",
                must_master=["输入信号", "数学变换", "频域结果", "性质关系"],
                source_formulas=[{"name": "F(w)"}, {"name": "inverse"}],
            )
        )

        self.assertTrue(plan.need_visual)
        self.assertGreaterEqual(plan.complexity, 0.6)

    def test_simple_low_importance_item_is_skipped(self):
        plan = VisualPlanner().plan(planner_snapshot(importance=2, content="Simple fact."))

        self.assertFalse(plan.need_visual)
        self.assertIsNone(plan.generator)

    def test_mermaid_v1_always_uses_compatible_flowchart(self):
        content = MermaidGenerator().generate(
            {
                "nodes": [
                    {"id": "n0", "label": 'Start "here"'},
                    {"id": "n1", "label": "<unsafe>"},
                ],
                "edges": [{"from": "n0", "to": "n1"}],
            }
        )

        self.assertTrue(content.startswith("flowchart TD"))
        self.assertNotIn("mindmap", content)
        self.assertNotIn("click", content)
        self.assertNotIn("<unsafe>", content)

    def test_svg_generator_returns_self_contained_safe_svg(self):
        content = SvgGenerator().generate(
            {
                "title": "Diagram",
                "nodes": [{"id": "n0", "label": "<script>alert(1)</script>"}],
                "edges": [],
            }
        )

        self.assertTrue(content.startswith("<svg"))
        self.assertNotIn("<script>", content)
        self.assertNotIn("foreignObject", content)

    def test_source_hash_is_deterministic_and_versioned(self):
        first = build_source_hash(planner_snapshot())
        second = build_source_hash(planner_snapshot())
        changed = build_source_hash(planner_snapshot(title="Laplace transform"))

        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)


class VisualServiceAndApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    def setUp(self):
        with get_db_session() as session:
            session.execute(delete(VisualAsset))
            session.execute(delete(Task).where(Task.resource_type == "visual_asset"))
            user = User(
                email="visual-owner@example.com",
                password_hash="test",
            )
            other = User(
                email="visual-other@example.com",
                password_hash="test",
            )
            session.add_all([user, other])
            session.flush()
            course = Course(user_id=user.id, name="Signals")
            session.add(course)
            session.flush()
            document = Document(
                user_id=user.id,
                course_id=course.id,
                original_filename="signals.pdf",
                stored_filename="signals.pdf",
                file_path="signals.pdf",
                mime_type="application/pdf",
                file_size=100,
                processing_status="completed",
                document_type="SLIDES",
            )
            session.add(document)
            session.flush()
            analysis = DocumentAnalysis(
                document_id=document.id,
                summary="Signals summary",
                topics=[
                    {
                        "name": "Fourier transform",
                        "importance": 5,
                        "core_explanation": "首先输入时域信号，然后执行变换，最后得到频域结果。",
                        "must_master": ["Input", "Transform", "Output"],
                    }
                ],
                importance_map={"Fourier transform": 5},
                analysis_json={"formulas": [{"name": "F(w)"}]},
            )
            session.add(analysis)
            session.flush()
            self.user_id = user.id
            self.other_user_id = other.id
            self.course_id = course.id
            self.document_id = document.id
            self.target_id = f"analysis-{analysis.id}-topic-0"

    def tearDown(self):
        with get_db_session() as session:
            for email in ("visual-owner@example.com", "visual-other@example.com"):
                user = session.scalar(select(User).where(User.email == email))
                if user is not None:
                    session.delete(user)

    def test_request_persists_snapshot_hash_and_task_idempotently(self):
        service = VisualService()
        asset, plan = service.request_generation(
            "knowledge_item",
            self.target_id,
            self.user_id,
        )
        repeated, _ = service.request_generation(
            "knowledge_item",
            self.target_id,
            self.user_id,
        )

        self.assertTrue(plan.need_visual)
        self.assertEqual(asset.id, repeated.id)
        self.assertEqual(asset.target_id, self.target_id)
        self.assertEqual(asset.target_snapshot["title"], "Fourier transform")
        self.assertEqual(len(asset.source_hash), 64)
        self.assertEqual(asset.task.status, "PENDING")

    def test_worker_claim_and_generation_complete_both_lifecycles(self):
        asset, _ = VisualService().request_generation(
            "knowledge_item",
            self.target_id,
            self.user_id,
        )

        claimed = worker._claim_next_visual()
        self.assertEqual(claimed[0], asset.id)
        worker._process_claimed_visual(claimed)

        with get_db_session() as session:
            stored = session.get(VisualAsset, asset.id)
            task = session.get(Task, stored.task_id)
            self.assertEqual(stored.status, "completed")
            self.assertTrue(stored.content.startswith("flowchart TD"))
            self.assertEqual(task.status, "SUCCESS")
            self.assertEqual(task.progress, 100)

    def test_worker_failure_retries_then_marks_task_failed(self):
        asset, _ = VisualService().request_generation(
            "knowledge_item",
            self.target_id,
            self.user_id,
        )

        class FailingVisualService:
            def process_asset(self, _asset_id):
                raise RuntimeError("visual generator failed")

        with patch("worker.VisualService", return_value=FailingVisualService()):
            first = worker._claim_next_visual()
            worker._process_claimed_visual(first)
            with get_db_session() as session:
                stored = session.get(VisualAsset, asset.id)
                self.assertEqual(stored.status, "pending")
                self.assertEqual(stored.task.status, "PENDING")

            second = worker._claim_next_visual()
            worker._process_claimed_visual(second)

        with get_db_session() as session:
            stored = session.get(VisualAsset, asset.id)
            self.assertEqual(stored.status, "failed")
            self.assertEqual(stored.task.status, "FAILED")
            self.assertEqual(stored.error_code, "RuntimeError")

    def test_api_hides_other_users_target_and_returns_current_asset(self):
        current_user = type(
            "CurrentUser",
            (),
            {
                "id": self.user_id,
                "email": "visual-owner@example.com",
                "created_at": datetime.now(timezone.utc),
            },
        )()
        client = TestClient(create_app(session_secret="visual-test-secret"))
        with (
            patch("src.api.dependencies.get_user_by_email", return_value=current_user),
            client,
        ):
            client.cookies.set("learning_os_session", "")
            with patch("src.api.routers.auth.authenticate_user", return_value=current_user):
                client.post(
                    "/api/auth/login",
                    json={"email": current_user.email, "password": "secret"},
                )
            response = client.post(
                f"/api/visual-assets/knowledge_item/{self.target_id}"
            )
            listed = client.get(
                f"/api/visual-assets/knowledge_item/{self.target_id}"
            )

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.json()["recommended"])
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()["items"]), 1)

        other_user = type(
            "OtherUser",
            (),
            {
                "id": self.other_user_id,
                "email": "visual-other@example.com",
                "created_at": datetime.now(timezone.utc),
            },
        )()
        other_client = TestClient(create_app(session_secret="visual-test-secret"))
        with (
            patch("src.api.dependencies.get_user_by_email", return_value=other_user),
            other_client,
        ):
            with patch("src.api.routers.auth.authenticate_user", return_value=other_user):
                other_client.post(
                    "/api/auth/login",
                    json={"email": other_user.email, "password": "secret"},
                )
            hidden = other_client.get(
                f"/api/visual-assets/knowledge_item/{self.target_id}"
            )

        self.assertEqual(hidden.status_code, 404)


if __name__ == "__main__":
    unittest.main()

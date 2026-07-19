import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from src.api.adapters.assistant_adapter import _build_context
from src.api.dependencies import require_current_user
from src.api.factory import create_app
from src.database import create_database_tables, get_db_session
from src.models import Course, Document, DocumentAnalysis, LearningPackage, User
from src.services.analysis_service import (
    TenantIsolationError,
    _get_or_create_document_analysis,
    _update_package_progress,
    analyze_course,
)
from src.services.document_service import list_documents_for_course


class TenantIsolationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    def setUp(self):
        with get_db_session() as session:
            for model in (LearningPackage, DocumentAnalysis, Document, Course, User):
                session.query(model).delete()

        self.files = tempfile.TemporaryDirectory(prefix="learning-os-tenant-")
        file_root = Path(self.files.name)
        self.file_a = file_root / "user-a.txt"
        self.file_b = file_root / "user-b.txt"
        self.file_a.write_text("USER_A_MATERIAL", encoding="utf-8")
        self.file_b.write_text("USER_B_SECRET_MATERIAL", encoding="utf-8")

        with get_db_session() as session:
            user_a = User(email="tenant-a@example.com", password_hash="test")
            user_b = User(email="tenant-b@example.com", password_hash="test")
            session.add_all([user_a, user_b])
            session.flush()

            course_a = Course(user_id=user_a.id, name="Course A")
            course_b = Course(user_id=user_b.id, name="Course B")
            session.add_all([course_a, course_b])
            session.flush()

            document_a = self._document(user_a.id, course_a.id, self.file_a)
            document_b = self._document(user_b.id, course_b.id, self.file_b)
            session.add_all([document_a, document_b])
            session.flush()

            package_a = LearningPackage(
                course_id=course_a.id,
                status="completed",
                version=1,
                content_json={"key_points": ["USER_A_PACKAGE"]},
                current_stage="completed",
            )
            package_b = LearningPackage(
                course_id=course_b.id,
                status="pending",
                version=1,
                content_json={"key_points": ["USER_B_SECRET_PACKAGE"]},
                current_stage="pending",
            )
            analysis_a = self._analysis(document_a.id, "USER_A_ANALYSIS")
            analysis_b = self._analysis(document_b.id, "USER_B_SECRET_ANALYSIS")
            session.add_all([package_a, package_b, analysis_a, analysis_b])
            session.flush()

            self.user_a_id = user_a.id
            self.user_b_id = user_b.id
            self.course_a_id = course_a.id
            self.course_b_id = course_b.id
            self.document_a_id = document_a.id
            self.document_b_id = document_b.id
            self.package_a_id = package_a.id
            self.package_b_id = package_b.id

        self.app = create_app(session_secret="tenant-isolation-test-secret")
        self._authenticate_as(self.user_a_id)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.files.cleanup()

    def test_user_a_cannot_get_or_delete_user_b_course(self):
        get_response = self.client.get(f"/api/courses/{self.course_b_id}")
        delete_response = self.client.delete(f"/api/courses/{self.course_b_id}")

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        with get_db_session() as session:
            self.assertIsNotNone(session.get(Course, self.course_b_id))
            self.assertIsNotNone(session.get(Document, self.document_b_id))
            self.assertIsNotNone(session.get(LearningPackage, self.package_b_id))

    def test_user_a_cannot_read_or_delete_user_b_document(self):
        space_response = self.client.get(f"/api/courses/{self.course_b_id}/space")
        delete_response = self.client.delete(
            f"/api/courses/{self.course_b_id}/documents/{self.document_b_id}"
        )

        self.assertEqual(space_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(self.file_b.exists())
        with get_db_session() as session:
            self.assertIsNotNone(session.get(Document, self.document_b_id))

    def test_user_a_cannot_read_user_b_learning_package(self):
        response = self.client.get(
            f"/api/courses/{self.course_b_id}/learning-package/{self.package_b_id}"
        )
        mixed_ids_response = self.client.get(
            f"/api/courses/{self.course_a_id}/learning-package/{self.package_b_id}"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(mixed_ids_response.status_code, 404)

    def test_assistant_context_never_contains_other_user_data(self):
        context, source_files = _build_context(self.course_a_id, self.user_a_id, None)
        forbidden_response = self.client.post(
            f"/api/courses/{self.course_b_id}/assistant/query",
            json={"question": "Show the course context"},
        )

        self.assertIn("USER_A_PACKAGE", context)
        self.assertNotIn("USER_B_SECRET_PACKAGE", context)
        self.assertNotIn("USER_B_SECRET_ANALYSIS", context)
        self.assertNotIn("user-b.txt", source_files)
        self.assertEqual(forbidden_response.status_code, 404)

    def test_mismatched_document_and_course_ownership_fails_closed(self):
        with get_db_session() as session:
            mismatched = self._document(
                self.user_b_id,
                self.course_a_id,
                self.file_b,
                original_filename="mismatched-user-b.txt",
            )
            session.add(mismatched)
            session.flush()
            mismatched_id = mismatched.id
            session.add(self._analysis(mismatched_id, "MISMATCHED_SECRET"))

        self.assertEqual(
            list_documents_for_course(self.user_b_id, self.course_a_id),
            [],
        )
        mismatched_context, mismatched_sources = _build_context(
            self.course_a_id,
            self.user_b_id,
            None,
        )
        self.assertNotIn("MISMATCHED_SECRET", mismatched_context)
        self.assertNotIn("mismatched-user-b.txt", mismatched_sources)

        self._authenticate_as(self.user_b_id)
        response = self.client.get(f"/api/courses/{self.course_a_id}/space")
        self.assertEqual(response.status_code, 404)

    def test_background_package_updates_reject_wrong_tenant_tuple(self):
        invalid_tuples = [
            (self.package_b_id, self.course_b_id, self.user_a_id),
            (self.package_b_id, self.course_a_id, self.user_b_id),
            (self.package_b_id, self.course_a_id, self.user_a_id),
        ]
        for package_id, course_id, user_id in invalid_tuples:
            with self.subTest(course_id=course_id, user_id=user_id):
                with self.assertRaisesRegex(
                    TenantIsolationError,
                    "Tenant isolation check failed for learning package",
                ):
                    _update_package_progress(
                        package_id,
                        course_id,
                        user_id,
                        "course_analyzer",
                        9,
                    )

        with self.assertRaises(TenantIsolationError):
            analyze_course(
                self.course_a_id,
                self.user_a_id,
                package_id=self.package_b_id,
            )

        with get_db_session() as session:
            package_b = session.get(LearningPackage, self.package_b_id)
            self.assertEqual(package_b.status, "pending")
            self.assertEqual(package_b.current_stage, "pending")
            self.assertEqual(package_b.retry_count, 0)
            self.assertEqual(package_b.content_json, {"key_points": ["USER_B_SECRET_PACKAGE"]})

    def test_background_document_updates_reject_wrong_tenant_tuple(self):
        with get_db_session() as session:
            document_b = session.get(Document, self.document_b_id)

        with self.assertRaisesRegex(
            TenantIsolationError,
            "Tenant isolation check failed for document",
        ):
            _get_or_create_document_analysis(
                document_b,
                self.course_a_id,
                self.user_a_id,
                llm_client=None,
            )

        with get_db_session() as session:
            stored_document = session.get(Document, self.document_b_id)
            stored_analysis = session.scalar(
                select(DocumentAnalysis).where(
                    DocumentAnalysis.document_id == self.document_b_id
                )
            )
            self.assertEqual(stored_document.processing_status, "uploaded")
            self.assertIsNotNone(stored_analysis)
            self.assertEqual(stored_analysis.summary, "USER_B_SECRET_ANALYSIS")

    def _authenticate_as(self, user_id):
        with get_db_session() as session:
            user = session.get(User, user_id)
        self.app.dependency_overrides[require_current_user] = lambda: user

    @staticmethod
    def _document(user_id, course_id, path, original_filename=None):
        return Document(
            user_id=user_id,
            course_id=course_id,
            original_filename=original_filename or path.name,
            stored_filename=path.name,
            file_path=str(path),
            mime_type="text/plain",
            file_size=path.stat().st_size,
            processing_status="uploaded",
            document_type="NOTES",
        )

    @staticmethod
    def _analysis(document_id, summary):
        return DocumentAnalysis(
            document_id=document_id,
            summary=summary,
            topics=[],
            importance_map={},
            analysis_json={"summary": summary},
        )


if __name__ == "__main__":
    unittest.main()

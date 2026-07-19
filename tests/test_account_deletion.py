import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select

from src.api.factory import create_app
from src.config import BASE_DIR, UPLOAD_DIR
from src.database import create_database_tables, get_db_session
from src.models import (
    Course,
    Document,
    DocumentAnalysis,
    Knowledge,
    KnowledgeView,
    LearningPackage,
    User,
)
from src.services.account_deletion_service import (
    ACCOUNT_DELETION_CONFIRMATION,
    AccountDeletionService,
)
from src.services.document_service import save_uploaded_document
from src.services.user_service import register_user


class FakeUploadedFile:
    def __init__(self, name, data):
        self.name = name
        self.type = "text/plain"
        self._data = data

    def getvalue(self):
        return self._data


class AccountDeletionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    def setUp(self):
        with get_db_session() as session:
            for model in (
                KnowledgeView,
                Knowledge,
                LearningPackage,
                DocumentAnalysis,
                Document,
                Course,
                User,
            ):
                session.query(model).delete()

        self.user_a = register_user("delete-a@example.com", "password-a")
        self.user_b = register_user("delete-b@example.com", "password-b")
        with get_db_session() as session:
            course_a = Course(user_id=self.user_a.id, name="Course A")
            course_b = Course(user_id=self.user_b.id, name="Course B")
            session.add_all([course_a, course_b])
            session.flush()
            self.course_a_id = course_a.id
            self.course_b_id = course_b.id

        document_a = save_uploaded_document(
            self.user_a.id,
            self.course_a_id,
            FakeUploadedFile("a.txt", b"user a material"),
            "NOTES",
        )
        document_b = save_uploaded_document(
            self.user_b.id,
            self.course_b_id,
            FakeUploadedFile("b.txt", b"user b material"),
            "NOTES",
        )
        self.document_a_id = document_a.id
        self.document_b_id = document_b.id
        self.file_a = self._resolve_path(document_a.file_path)
        self.file_b = self._resolve_path(document_b.file_path)

        with get_db_session() as session:
            session.add_all(
                [
                    DocumentAnalysis(
                        document_id=self.document_a_id,
                        summary="A analysis",
                        topics=[],
                        importance_map={},
                        analysis_json={},
                    ),
                    DocumentAnalysis(
                        document_id=self.document_b_id,
                        summary="B analysis",
                        topics=[],
                        importance_map={},
                        analysis_json={},
                    ),
                    LearningPackage(
                        course_id=self.course_a_id,
                        status="completed",
                        version=1,
                        content_json={"owner": "A"},
                    ),
                    LearningPackage(
                        course_id=self.course_b_id,
                        status="completed",
                        version=1,
                        content_json={"owner": "B"},
                    ),
                    Knowledge(
                        user_id=self.user_a.id,
                        course_id=self.course_a_id,
                        content_json={"owner": "A"},
                    ),
                    Knowledge(
                        user_id=self.user_b.id,
                        course_id=self.course_b_id,
                        content_json={"owner": "B"},
                    ),
                    KnowledgeView(user_id=self.user_a.id, knowledge_key="a:1"),
                    KnowledgeView(user_id=self.user_b.id, knowledge_key="b:1"),
                ]
            )
            session.flush()
            self.analysis_a_id = session.scalar(
                select(DocumentAnalysis.id).where(
                    DocumentAnalysis.document_id == self.document_a_id
                )
            )

        self.client = TestClient(create_app(session_secret="account-deletion-test-secret"))
        self._login_as_user_a()

    def tearDown(self):
        self.client.close()
        for user_id in (self.user_a.id, self.user_b.id):
            shutil.rmtree(UPLOAD_DIR / f"user_{user_id}", ignore_errors=True)

    def test_user_a_deletes_account_and_all_owned_data_without_affecting_user_b(self):
        response = self.client.request(
            "DELETE",
            "/api/account",
            json={
                "password": "password-a",
                "confirmation": ACCOUNT_DELETION_CONFIRMATION,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "deleted")
        self.assertFalse(self.file_a.exists())
        self.assertTrue(self.file_b.exists())

        with get_db_session() as session:
            self.assertIsNone(session.get(User, self.user_a.id))
            self.assertEqual(
                session.scalar(select(Course).where(Course.user_id == self.user_a.id)),
                None,
            )
            self.assertEqual(
                session.scalar(select(Document).where(Document.user_id == self.user_a.id)),
                None,
            )
            self.assertEqual(
                session.scalar(select(Knowledge).where(Knowledge.user_id == self.user_a.id)),
                None,
            )
            self.assertIsNone(session.get(DocumentAnalysis, self.analysis_a_id))
            self.assertEqual(
                session.scalar(
                    select(LearningPackage).where(
                        LearningPackage.course_id == self.course_a_id
                    )
                ),
                None,
            )
            self.assertEqual(
                session.scalar(
                    select(KnowledgeView).where(KnowledgeView.user_id == self.user_a.id)
                ),
                None,
            )
            self.assertIsNotNone(session.get(User, self.user_b.id))
            self.assertIsNotNone(session.get(Course, self.course_b_id))
            self.assertIsNotNone(session.get(Document, self.document_b_id))
            self.assertIsNotNone(
                session.scalar(
                    select(DocumentAnalysis).where(
                        DocumentAnalysis.document_id == self.document_b_id
                    )
                )
            )
            self.assertIsNotNone(
                session.scalar(
                    select(LearningPackage).where(
                        LearningPackage.course_id == self.course_b_id
                    )
                )
            )

    def test_deleted_user_is_logged_out_and_cannot_log_in_again(self):
        response = self.client.request(
            "DELETE",
            "/api/account",
            json={
                "password": "password-a",
                "confirmation": ACCOUNT_DELETION_CONFIRMATION,
            },
        )
        self.assertEqual(response.status_code, 200)

        me_response = self.client.get("/api/auth/me")
        login_response = self.client.post(
            "/api/auth/login",
            json={"email": "delete-a@example.com", "password": "password-a"},
        )
        self.assertEqual(me_response.status_code, 401)
        self.assertEqual(login_response.status_code, 401)

    def test_wrong_confirmation_cannot_delete_any_account(self):
        response = self.client.request(
            "DELETE",
            "/api/account",
            json={"password": "password-a", "confirmation": "DELETE"},
        )

        self.assertEqual(response.status_code, 400)
        with get_db_session() as session:
            self.assertIsNotNone(session.get(User, self.user_a.id))
            self.assertIsNotNone(session.get(User, self.user_b.id))
        self.assertTrue(self.file_a.exists())
        self.assertTrue(self.file_b.exists())

    def test_database_failure_restores_quarantined_files_and_user_data(self):
        service = AccountDeletionService()
        with patch.object(
            AccountDeletionService,
            "_delete_user_records",
            side_effect=RuntimeError("database failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "database failure"):
                service.delete_current_user(
                    self.user_a.id,
                    "password-a",
                    ACCOUNT_DELETION_CONFIRMATION,
                )

        with get_db_session() as session:
            self.assertIsNotNone(session.get(User, self.user_a.id))
            self.assertIsNotNone(session.get(Document, self.document_a_id))
        self.assertTrue(self.file_a.exists())

    def test_file_cleanup_failure_is_logged_after_transactional_deletion(self):
        with tempfile.NamedTemporaryFile(prefix="learning-os-legacy-", delete=False) as file:
            legacy_file = Path(file.name)
        self.addCleanup(legacy_file.unlink, missing_ok=True)
        with get_db_session() as session:
            session.add(
                Document(
                    user_id=self.user_a.id,
                    course_id=self.course_a_id,
                    original_filename="legacy.txt",
                    stored_filename="legacy.txt",
                    file_path=str(legacy_file),
                    mime_type="text/plain",
                    file_size=0,
                    processing_status="uploaded",
                    document_type="NOTES",
                )
            )

        service = AccountDeletionService()
        with self.assertLogs(
            "src.services.account_deletion_service",
            level="ERROR",
        ) as logs:
            result = service.delete_current_user(
                self.user_a.id,
                "password-a",
                ACCOUNT_DELETION_CONFIRMATION,
            )

        self.assertEqual(result.file_cleanup_error_count, 1)
        self.assertTrue(legacy_file.exists())
        self.assertTrue(
            any("Failed to delete an account document file." in item for item in logs.output)
        )

    def _login_as_user_a(self):
        response = self.client.post(
            "/api/auth/login",
            json={"email": "delete-a@example.com", "password": "password-a"},
        )
        self.assertEqual(response.status_code, 200)

    @staticmethod
    def _resolve_path(file_path):
        path = Path(file_path)
        return path.resolve() if path.is_absolute() else (BASE_DIR / path).resolve()


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest
from pathlib import Path

import fitz


TEST_DIR = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(TEST_DIR.name) / 'test.db').as_posix()}"

from src.database import create_database_tables, get_db_session  # noqa: E402
from src.database.connection import engine  # noqa: E402
from src.models import Course, Document, DocumentAnalysis, LearningPackage, User  # noqa: E402
from src.services.analysis_service import analyze_course, get_learning_package  # noqa: E402


class FakeLLMClient:
    def generate(self, system_prompt, user_prompt):
        if "document_type" in user_prompt:
            return {
                "summary": "Test summary",
                "topics": ["Core topic"],
                "importance_map": {"Core topic": "high"},
            }
        if "knowledge_map" in system_prompt:
            return {
                "knowledge_map": {"Core topic": []},
                "chapter_relations": [],
                "priority_ranking": ["Core topic"],
            }
        return {
            "course_map": {"Core topic": []},
            "chapter_summary": ["Chapter summary"],
            "key_points": ["Core topic"],
            "formula_book": [],
            "exam_focus": ["Core topic"],
            "questions": [{"question": "Test?", "answer": "Yes"}],
        }


class AnalysisFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        TEST_DIR.cleanup()

    def test_course_analysis_persists_results(self):
        pdf_path = Path(TEST_DIR.name) / "course.pdf"
        with fitz.open() as pdf:
            page = pdf.new_page()
            page.insert_text((72, 72), "Core topic and formula F = ma")
            pdf.save(pdf_path)

        with get_db_session() as session:
            user = User(email="student@example.com", password_hash="test")
            session.add(user)
            session.flush()
            course = Course(user_id=user.id, name="Physics")
            session.add(course)
            session.flush()
            document = Document(
                user_id=user.id,
                course_id=course.id,
                original_filename="course.pdf",
                stored_filename="course.pdf",
                file_path=str(pdf_path),
                mime_type="application/pdf",
                file_size=pdf_path.stat().st_size,
                document_type="TEXTBOOK",
            )
            session.add(document)
            session.flush()
            user_id, course_id = user.id, course.id

        package = analyze_course(course_id, user_id, llm_client=FakeLLMClient())
        self.assertEqual(package.status, "completed")
        self.assertIn("course_map", package.content_json)
        latest = get_learning_package(course_id, user_id)
        self.assertEqual(latest.id, package.id)

        with get_db_session() as session:
            self.assertEqual(session.query(DocumentAnalysis).count(), 1)
            self.assertEqual(session.query(LearningPackage).count(), 1)


if __name__ == "__main__":
    unittest.main()

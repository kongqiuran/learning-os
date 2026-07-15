import tempfile
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

from src.api.adapters import knowledge_adapter
from src.api.adapters.knowledge_adapter import (
    create_knowledge_key,
    get_knowledge_item,
    list_course_knowledge,
    mark_knowledge_viewed,
    parse_knowledge_key,
)
from src.database.base import Base
from src.models import Course, Document, DocumentAnalysis, KnowledgeView, User


TEST_DIR = tempfile.TemporaryDirectory()
TEST_ENGINE = create_engine(
    f"sqlite:///{TEST_DIR.name}/knowledge.db",
    connect_args={"check_same_thread": False},
)
TEST_SESSION = sessionmaker(bind=TEST_ENGINE, autoflush=False, expire_on_commit=False)


@contextmanager
def get_test_session():
    session = TEST_SESSION()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class KnowledgeAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=TEST_ENGINE)

    @classmethod
    def tearDownClass(cls):
        TEST_ENGINE.dispose()
        TEST_DIR.cleanup()

    def setUp(self):
        self.session_patch = patch.object(knowledge_adapter, "get_db_session", get_test_session)
        self.session_patch.start()
        with get_test_session() as session:
            user = User(email=f"knowledge-{id(self)}@example.com", password_hash="hash")
            session.add(user)
            session.flush()
            course = Course(user_id=user.id, name="Signals", description=None)
            session.add(course)
            session.flush()
            document = Document(
                user_id=user.id,
                course_id=course.id,
                original_filename="lecture.md",
                stored_filename="stored.md",
                file_path="test.md",
                mime_type="text/markdown",
                file_size=100,
                processing_status="completed",
                document_type="NOTES",
            )
            session.add(document)
            session.flush()
            analysis = DocumentAnalysis(
                document_id=document.id,
                summary="Document summary",
                topics=[
                    {
                        "name": "Fourier transform",
                        "importance": 5,
                        "core_explanation": "Transforms a signal into frequency components.",
                        "exam_value": "Used in calculation questions.",
                        "must_master": ["Definition", "Shift property"],
                        "memory_tips": "Think in frequency components.",
                        "reason": "Central concept",
                    }
                ],
                importance_map={"Fourier transform": 5},
                analysis_json={
                    "formulas": [{"name": "Definition", "formula": "X(f)=integral"}],
                    "errors": ["Confusing time and frequency shifts"],
                },
            )
            session.add(analysis)
            session.flush()
            self.user_id = user.id
            self.course = course
            self.analysis_id = analysis.id

    def tearDown(self):
        with get_test_session() as session:
            session.execute(delete(KnowledgeView).where(KnowledgeView.user_id == self.user_id))
            session.execute(
                delete(DocumentAnalysis).where(
                    DocumentAnalysis.document_id.in_(
                        select(Document.id).where(Document.user_id == self.user_id)
                    )
                )
            )
            session.execute(delete(Document).where(Document.user_id == self.user_id))
            session.execute(delete(Course).where(Course.user_id == self.user_id))
            session.execute(delete(User).where(User.id == self.user_id))
        self.session_patch.stop()

    def test_topics_are_mapped_without_copying_knowledge_rows(self):
        items = list_course_knowledge(self.course, self.user_id)

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.id, create_knowledge_key(self.analysis_id, 0))
        self.assertEqual(item.title, "Fourier transform")
        self.assertEqual(item.content, "Transforms a signal into frequency components.")
        self.assertEqual(item.importance, 5)
        self.assertEqual(item.source_file, "lecture.md")
        self.assertEqual(item.source_formulas[0]["name"], "Definition")

    def test_course_without_analysis_returns_empty_list(self):
        with get_test_session() as session:
            empty_course = Course(user_id=self.user_id, name="Empty course", description=None)
            session.add(empty_course)
            session.flush()

        self.assertEqual(list_course_knowledge(empty_course, self.user_id), [])

    def test_detail_is_resolved_from_analysis_and_topic_index(self):
        item = get_knowledge_item(create_knowledge_key(self.analysis_id, 0), self.user_id)

        self.assertIsNotNone(item)
        self.assertEqual(item.must_master, ["Definition", "Shift property"])
        self.assertEqual(item.source_errors, ["Confusing time and frequency shifts"])

    def test_viewed_state_persists_across_database_sessions(self):
        key = create_knowledge_key(self.analysis_id, 0)
        viewed_at = mark_knowledge_viewed(key, self.user_id)

        self.assertIsNotNone(viewed_at)
        with get_test_session() as session:
            persisted = session.scalar(
                select(KnowledgeView).where(
                    KnowledgeView.user_id == self.user_id,
                    KnowledgeView.knowledge_key == key,
                )
            )
        self.assertIsNotNone(persisted)
        reloaded = get_knowledge_item(key, self.user_id)
        self.assertTrue(reloaded.viewed)

    def test_mark_viewed_is_idempotent(self):
        key = create_knowledge_key(self.analysis_id, 0)
        mark_knowledge_viewed(key, self.user_id)
        mark_knowledge_viewed(key, self.user_id)

        with get_test_session() as session:
            views = list(
                session.scalars(
                    select(KnowledgeView).where(
                        KnowledgeView.user_id == self.user_id,
                        KnowledgeView.knowledge_key == key,
                    )
                )
            )
        self.assertEqual(len(views), 1)

    def test_other_user_cannot_read_or_mark_knowledge(self):
        key = create_knowledge_key(self.analysis_id, 0)
        self.assertIsNone(get_knowledge_item(key, self.user_id + 9999))
        self.assertIsNone(mark_knowledge_viewed(key, self.user_id + 9999))

    def test_key_parser_reserves_future_analysis_version(self):
        current = parse_knowledge_key(f"analysis-{self.analysis_id}-topic-0")
        future = parse_knowledge_key(f"analysis-{self.analysis_id}-version-2-topic-0")

        self.assertIsNone(current.analysis_version)
        self.assertEqual(future.analysis_version, 2)


if __name__ == "__main__":
    unittest.main()

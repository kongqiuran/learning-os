import unittest
from datetime import datetime, timedelta, timezone

from src.database import create_database_tables, get_db_session
from src.models import CourseEntitlement, Document, User
from src.services.chapter_service import create_chapter, delete_chapter, move_document
from src.services.course_service import create_course
from src.services.entitlement_service import consume_assistant, consume_scene, get_active_entitlement
from src.services.user_service import register_user


class V2FeatureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    def setUp(self):
        with get_db_session() as session:
            session.query(User).delete()
        self.user = register_user(f"v2-{id(self)}@example.com", "password")
        self.course = create_course(self.user.id, "Signals")

    def test_chapter_delete_requires_explicit_material_action_and_can_keep_documents(self):
        chapter = create_chapter(self.course.id, self.user.id, "Chapter One")
        with get_db_session() as session:
            document = Document(user_id=self.user.id, course_id=self.course.id, chapter_id=chapter.id, original_filename="lecture.md", stored_filename="lecture.md", file_path="data/uploads/missing.md", mime_type="text/markdown", file_size=4, document_type="SLIDES")
            session.add(document); session.flush(); document_id = document.id
        with self.assertRaises(ValueError):
            delete_chapter(chapter.id, self.course.id, self.user.id, "")
        self.assertTrue(delete_chapter(chapter.id, self.course.id, self.user.id, "keep_unassigned"))
        with get_db_session() as session:
            self.assertIsNone(session.get(Document, document_id).chapter_id)

    def test_course_entitlement_consumes_successful_scene_and_assistant_allowances(self):
        with get_db_session() as session:
            item = CourseEntitlement(user_id=self.user.id, course_id=self.course.id, payment_reference="manual-test", expires_at=datetime.now(timezone.utc) + timedelta(days=90))
            session.add(item); session.flush(); entitlement_id = item.id
        active = get_active_entitlement(self.user.id, self.course.id)
        self.assertEqual(active.id, entitlement_id)
        consume_scene(entitlement_id, "follow")
        consume_assistant(self.user.id, self.course.id)
        with get_db_session() as session:
            stored = session.get(CourseEntitlement, entitlement_id)
            self.assertEqual(stored.follow_remaining, 2)
            self.assertEqual(stored.assistant_remaining, 99)


if __name__ == "__main__":
    unittest.main()

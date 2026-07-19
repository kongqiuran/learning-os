import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from src.database import create_database_tables, get_db_session
from src.billing.product_catalog import get_billing_product
from src.models import CourseEntitlement, Document, LearningPackage, Task, User
from src.services.chapter_service import create_chapter, delete_chapter, move_document
from src.services.course_service import create_course
from src.services.entitlement_service import EntitlementQuotaExceeded, consume_assistant, consume_scene, get_active_entitlement, reserve_scene
from src.services.quota_settlement_service import release_package_quota
from src.services.user_service import register_user


def entitlement_values():
    product = get_billing_product("course_space")
    return {
        "product_code": product.product_code,
        "amount_cents": product.amount_cents,
        "follow_remaining": product.follow_allowance,
        "textbook_remaining": product.textbook_allowance,
        "exam_remaining": product.exam_allowance,
        "assistant_remaining": product.assistant_allowance,
    }


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
            item = CourseEntitlement(user_id=self.user.id, course_id=self.course.id, payment_reference="manual-test", expires_at=datetime.now(timezone.utc) + timedelta(days=90), **entitlement_values())
            session.add(item); session.flush(); entitlement_id = item.id
        active = get_active_entitlement(self.user.id, self.course.id)
        self.assertEqual(active.id, entitlement_id)
        consume_scene(entitlement_id, "follow")
        consume_assistant(self.user.id, self.course.id)
        with get_db_session() as session:
            stored = session.get(CourseEntitlement, entitlement_id)
            product = get_billing_product("course_space")
            self.assertEqual(stored.follow_remaining, product.follow_allowance - 1)
            self.assertEqual(stored.assistant_remaining, product.assistant_allowance - 1)

    def test_scene_reservation_is_atomic_when_one_allowance_remains(self):
        with get_db_session() as session:
            values = entitlement_values()
            values["follow_remaining"] = 1
            item = CourseEntitlement(user_id=self.user.id, course_id=self.course.id, payment_reference="atomic-test", expires_at=datetime.now(timezone.utc) + timedelta(days=90), **values)
            session.add(item); session.flush(); entitlement_id = item.id

        def attempt_reservation(_index):
            try:
                reserve_scene(entitlement_id, "follow")
                return True
            except EntitlementQuotaExceeded:
                return False

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt_reservation, range(2)))

        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 1)
        with get_db_session() as session:
            self.assertEqual(session.get(CourseEntitlement, entitlement_id).follow_remaining, 0)

    def test_package_quota_refund_is_idempotent(self):
        with get_db_session() as session:
            values = entitlement_values()
            values["follow_remaining"] = 1
            item = CourseEntitlement(user_id=self.user.id, course_id=self.course.id, payment_reference="refund-test", expires_at=datetime.now(timezone.utc) + timedelta(days=90), **values)
            session.add(item); session.flush(); entitlement_id = item.id
        reserve_scene(entitlement_id, "follow")
        with get_db_session() as session:
            package = LearningPackage(course_id=self.course.id, status="failed", scene="follow", content_json={}, entitlement_id=entitlement_id, quota_source="course_entitlement", quota_state="reserved")
            session.add(package); session.flush(); package_id = package.id
        with get_db_session() as session:
            self.assertTrue(release_package_quota(session, package_id))
        with get_db_session() as session:
            self.assertFalse(release_package_quota(session, package_id))
            self.assertEqual(session.get(CourseEntitlement, entitlement_id).follow_remaining, 1)

    def test_worker_claim_is_atomic(self):
        import worker

        with get_db_session() as session:
            package = LearningPackage(course_id=self.course.id, status="pending", scene="legacy", content_json={})
            session.add(package); session.flush(); package_id = package.id
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _index: worker._claim_next(), range(2)))
        claimed = [item for item in results if item is not None]
        self.assertEqual(len(claimed), 1)
        self.assertEqual(claimed[0][0], package_id)
        with get_db_session() as session:
            stored = session.get(LearningPackage, package_id)
            self.assertIsNotNone(stored.task_id)
            self.assertEqual(session.get(Task, stored.task_id).status, "RUNNING")


if __name__ == "__main__":
    unittest.main()
